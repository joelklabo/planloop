"""Codebase context builder for analyzing project structure."""
from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from .state import Task


class TodoComment(BaseModel):
    """A TODO/FIXME/NOTE comment found in code."""

    file: str
    line: int
    type: Literal["TODO", "FIXME", "NOTE", "HACK"]
    text: str


class CodebaseContext(BaseModel):
    """Analyzed context about a codebase."""

    project_root: Path
    structure: dict[str, Any]  # File tree
    current_tasks: list[Task]
    recent_changes: list[str]  # Changed files from git
    todos: list[TodoComment]
    language_stats: dict[str, int]  # Extension -> count


class ContextBuilder:
    """Builds context about a codebase for LLM analysis."""

    # Default patterns to ignore
    DEFAULT_IGNORE_PATTERNS = [
        "__pycache__",
        ".git",
        ".pytest_cache",
        ".hypothesis",
        "node_modules",
        ".venv",
        "venv",
        ".egg-info",
        "*.pyc",
        "*.pyo",
        ".DS_Store",
    ]

    # TODO/FIXME/NOTE pattern
    TODO_PATTERN = re.compile(
        r'#\s*(TODO|FIXME|NOTE|HACK)[:\s]+(.+)',
        re.IGNORECASE
    )

    def __init__(
        self,
        project_root: Path,
        ignore_patterns: list[str] | None = None
    ):
        """Initialize context builder.

        Args:
            project_root: Root directory of the project
            ignore_patterns: Optional list of patterns to ignore (overrides defaults)
        """
        self.project_root = Path(project_root)
        self.ignore_patterns = ignore_patterns or self.DEFAULT_IGNORE_PATTERNS

        # Cache for expensive operations
        self._structure_cache: dict[str, dict[str, Any]] = {}
        self._todos_cache: list[TodoComment] | None = None
        self._git_history_cache: list[str] | None = None
        self._lang_stats_cache: dict[str, int] | None = None

    def build(self, depth: Literal["shallow", "medium", "deep"] = "medium") -> CodebaseContext:
        """Build codebase context at specified depth.

        Args:
            depth: How deep to analyze
                - shallow: Basic file structure and stats
                - medium: + TODO comments and git history
                - deep: + detailed file content analysis (future)

        Returns:
            CodebaseContext with analyzed information
        """
        # Basic structure (all depths)
        structure = self._build_structure(depth)
        language_stats = self._count_languages()

        # Get current tasks from session (if exists)
        current_tasks = self._load_current_tasks()

        # Medium and deep depths get more detail
        if depth in ("medium", "deep"):
            todos = self._extract_todos()
            recent_changes = self._get_git_history()
        else:
            todos = []
            recent_changes = []

        return CodebaseContext(
            project_root=self.project_root,
            structure=structure,
            current_tasks=current_tasks,
            recent_changes=recent_changes,
            todos=todos,
            language_stats=language_stats
        )

    def _should_ignore(self, path: Path) -> bool:
        """Check if path matches ignore patterns."""
        path_str = str(path.relative_to(self.project_root))

        for pattern in self.ignore_patterns:
            # Handle wildcards
            if "*" in pattern:
                import fnmatch
                if fnmatch.fnmatch(path_str, pattern):
                    return True
                if fnmatch.fnmatch(path.name, pattern):
                    return True
            # Exact directory/file name match
            elif pattern in path.parts:
                return True

        return False

    def _build_structure(self, depth: Literal["shallow", "medium", "deep"]) -> dict[str, Any]:
        """Build file structure tree."""
        # Check cache first
        if depth in self._structure_cache:
            return self._structure_cache[depth]

        structure: dict[str, Any] = {}

        # For shallow, limit depth to 2 levels
        max_depth = {"shallow": 2, "medium": 4, "deep": float("inf")}[depth]

        for path in self.project_root.rglob("*"):
            if self._should_ignore(path):
                continue

            # Check depth
            rel_path = path.relative_to(self.project_root)
            if len(rel_path.parts) > max_depth:
                continue

            # Build nested dict structure
            current = structure
            for part in rel_path.parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Add file or directory
            if path.is_file():
                current[rel_path.name] = "file"
            elif path.is_dir():
                if rel_path.name not in current:
                    current[rel_path.name] = {}

        # Cache the result
        self._structure_cache[depth] = structure
        return structure

    def _count_languages(self) -> dict[str, int]:
        """Count files by extension."""
        # Check cache
        if self._lang_stats_cache is not None:
            return self._lang_stats_cache

        stats: dict[str, int] = defaultdict(int)

        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue
            if self._should_ignore(path):
                continue

            # Get extension without dot
            ext = path.suffix[1:] if path.suffix else "no_extension"
            stats[ext] += 1

        # Cache and return
        self._lang_stats_cache = dict(stats)
        return self._lang_stats_cache

    def _extract_todos(self) -> list[TodoComment]:
        """Extract TODO/FIXME/NOTE comments from source files."""
        # Check cache
        if self._todos_cache is not None:
            return self._todos_cache

        todos: list[TodoComment] = []

        # Only scan text files (common source extensions)
        source_extensions = {".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".h"}

        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue
            if self._should_ignore(path):
                continue
            if path.suffix not in source_extensions:
                continue

            try:
                content = path.read_text(encoding="utf-8")
                for line_num, line in enumerate(content.splitlines(), start=1):
                    match = self.TODO_PATTERN.search(line)
                    if match:
                        todo_type = match.group(1).upper()
                        todo_text = match.group(2).strip()

                        todos.append(TodoComment(
                            file=str(path.relative_to(self.project_root)),
                            line=line_num,
                            type=todo_type,  # type: ignore  # Already validated by pattern
                            text=todo_text
                        ))
            except (UnicodeDecodeError, PermissionError):
                # Skip files that can't be read
                continue

        # Cache and return
        self._todos_cache = todos
        return todos

    def _get_git_history(self, limit: int = 10) -> list[str]:
        """Get recently changed files from git history."""
        # Check cache
        if self._git_history_cache is not None:
            return self._git_history_cache

        try:
            # Get list of changed files in last N commits
            result = subprocess.run(
                ["git", "log", f"--max-count={limit}", "--name-only", "--pretty=format:"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )

            # Parse output - skip empty lines and deduplicate
            files = []
            seen = set()
            for line in result.stdout.splitlines():
                line = line.strip()
                if line and line not in seen:
                    files.append(line)
                    seen.add(line)

            # Cache and return
            self._git_history_cache = files
            return files

        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # Not a git repo or git not available
            self._git_history_cache = []
            return []

    def _load_current_tasks(self) -> list[Task]:
        """Load current tasks from session if it exists."""
        try:
            # Try to find session in this project root
            # For now, just return empty - the suggest command will pass the session
            # This is a placeholder for future enhancement
            return []
        except Exception:
            return []
