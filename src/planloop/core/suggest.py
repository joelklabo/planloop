"""Suggestion engine for generating task suggestions from codebase analysis."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from ..config import SuggestConfig
from .context_builder import CodebaseContext, ContextBuilder
from .llm_client import LLMClient, LLMConfig
from .state import SessionState, TaskType


class TaskSuggestion(BaseModel):
    """A suggested task from codebase analysis."""

    title: str
    type: TaskType
    priority: Literal["low", "medium", "high"]
    rationale: str
    implementation_notes: str
    affected_files: list[str]
    depends_on: list[int] = []


class SuggestionEngine:
    """Generates task suggestions using LLM analysis of codebase."""

    def __init__(self, session: SessionState, config: SuggestConfig):
        """Initialize suggestion engine.

        Args:
            session: Current session state
            config: Suggestion configuration
        """
        self.session = session
        self.config = config

        # Initialize LLM client (lazy initialization to allow mocking in tests)
        self._llm_client: LLMClient | None = None

        # Get API key from environment if specified
        api_key = None
        if config.llm_api_key_env:
            api_key = os.environ.get(config.llm_api_key_env)

        self._llm_config = LLMConfig(
            provider=config.llm_provider,
            model=config.llm_model,
            api_key=api_key,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
            base_url=config.llm_base_url
        )

    @property
    def llm_client(self) -> LLMClient:
        """Lazy-initialize LLM client."""
        if self._llm_client is None:
            self._llm_client = LLMClient(self._llm_config)
        return self._llm_client

    def generate_suggestions(
        self,
        context: CodebaseContext | None = None,
        project_root: Path | None = None,
        depth: Literal["shallow", "medium", "deep"] | None = None
    ) -> list[TaskSuggestion]:
        """Generate task suggestions from codebase analysis.

        Args:
            context: Pre-built context (optional)
            project_root: Project root to analyze (if context not provided)
            depth: Analysis depth (if building context)

        Returns:
            List of validated task suggestions

        Raises:
            ValueError: If neither context nor project_root provided
        """
        # Build context if not provided
        if context is None:
            if project_root is None:
                raise ValueError("Must provide either context or project_root")

            depth = depth or self.config.context_depth
            builder = ContextBuilder(
                project_root,
                ignore_patterns=self.config.ignore_patterns
            )
            context = builder.build(depth=depth)

        # Build prompt
        prompt = self._build_prompt(context)

        # Get LLM suggestions
        try:
            schema = self._get_json_schema()
            raw_suggestions = self.llm_client.generate_json(prompt, schema)

            # Parse into TaskSuggestion objects
            suggestions = []
            for item in raw_suggestions:
                try:
                    suggestion = TaskSuggestion(**item)
                    suggestions.append(suggestion)
                except Exception:
                    # Skip invalid suggestions
                    continue

        except Exception as e:
            from .llm_client import LLMError
            raise LLMError(f"Failed to generate suggestions: {e}") from e

        # Validate and filter suggestions
        valid_suggestions = []
        for suggestion in suggestions:
            if self._validate_suggestion(suggestion):
                if not self._check_duplicates(suggestion):
                    valid_suggestions.append(suggestion)

        # Limit to max_suggestions
        return valid_suggestions[:self.config.max_suggestions]

    def _build_prompt(self, context: CodebaseContext) -> str:
        """Build prompt for LLM from context."""
        # Format current tasks
        current_tasks_str = "\n".join([
            f"- {task.id}: {task.title} ({task.type.value}, {task.status.value})"
            for task in self.session.tasks
        ])

        if not current_tasks_str:
            current_tasks_str = "(No current tasks)"

        # Format TODO comments
        todos_str = "\n".join([
            f"- {todo.file}:{todo.line} [{todo.type}] {todo.text}"
            for todo in context.todos[:10]  # Limit to avoid token overflow
        ])

        if not todos_str:
            todos_str = "(No TODO comments found)"

        # Format recent changes
        changes_str = "\n".join([
            f"- {change}"
            for change in context.recent_changes[:10]
        ])

        if not changes_str:
            changes_str = "(No recent changes)"

        # Format file structure (simplified)
        structure_str = json.dumps(context.structure, indent=2)[:500]  # Limit size

        # Format language stats
        lang_stats_str = ", ".join([
            f"{ext}: {count} files"
            for ext, count in sorted(context.language_stats.items(), key=lambda x: -x[1])[:5]
        ])

        prompt = f"""# Role
You are a technical project manager analyzing a codebase to suggest concrete, actionable tasks.

# Context
Session: {self.session.session}
Project Root: {context.project_root}
Language Stats: {lang_stats_str}

## Current Plan
{current_tasks_str}

## File Structure (partial)
{structure_str}

## Recent Changes
{changes_str}

## TODO Comments
{todos_str}

# Your Job
Analyze the codebase and suggest 3-5 high-impact tasks:
1. Find gaps (missing tests, docs, error handling)
2. Identify technical debt (TODOs, hacks, deprecated patterns)
3. Spot improvement opportunities (performance, security, UX)

# Rules
- Be specific (name files, functions, patterns)
- Prioritize based on impact and risk
- Check current plan for duplicates (avoid suggesting tasks already listed)
- Only suggest dependencies on existing task IDs
- Use appropriate task types: {", ".join([t.value for t in TaskType])}

# Output Format
Return a JSON array of TaskSuggestion objects. Each object must have:
- title: Clear, actionable task title
- type: One of the valid task types
- priority: "low", "medium", or "high"
- rationale: Why this task is important
- implementation_notes: Specific guidance on how to implement
- affected_files: List of files that would be changed
- depends_on: List of existing task IDs this depends on (can be empty)

Example:
[
  {{
    "title": "Add error handling to API endpoints",
    "type": "fix",
    "priority": "high",
    "rationale": "12 endpoints in src/api/routes.py lack try/catch blocks, risking unhandled exceptions",
    "implementation_notes": "Follow pattern from src/auth/routes.py - wrap handler logic in try/except, return 500 on errors",
    "affected_files": ["src/api/routes.py", "src/api/handlers.py"],
    "depends_on": []
  }}
]
"""

        return prompt

    def _get_json_schema(self) -> dict:
        """Get JSON schema for TaskSuggestion."""
        return {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "type": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "rationale": {"type": "string"},
                    "implementation_notes": {"type": "string"},
                    "affected_files": {"type": "array", "items": {"type": "string"}},
                    "depends_on": {"type": "array", "items": {"type": "integer"}}
                },
                "required": ["title", "type", "priority", "rationale", "implementation_notes", "affected_files"]
            }
        }

    def _validate_suggestion(self, suggestion: TaskSuggestion) -> bool:
        """Validate a suggestion is well-formed."""
        # Check title is not empty
        if not suggestion.title or not suggestion.title.strip():
            return False

        # Check rationale is not empty
        if not suggestion.rationale or not suggestion.rationale.strip():
            return False

        # Check implementation notes are not empty
        if not suggestion.implementation_notes or not suggestion.implementation_notes.strip():
            return False

        return True

    def _check_duplicates(self, suggestion: TaskSuggestion) -> bool:
        """Check if suggestion duplicates an existing task.

        Returns:
            True if duplicate, False if unique
        """
        # Simple title similarity check
        suggestion_title = suggestion.title.lower().strip()

        for task in self.session.tasks:
            task_title = task.title.lower().strip()

            # Exact match
            if suggestion_title == task_title:
                return True

            # Very similar (contains or is contained)
            if suggestion_title in task_title or task_title in suggestion_title:
                if len(suggestion_title) > 10 or len(task_title) > 10:
                    return True

        return False
