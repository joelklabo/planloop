"""Tests for suggestion engine."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from planloop.config import SuggestConfig
from planloop.core.context_builder import CodebaseContext, TodoComment
from planloop.core.state import SessionState, Task, TaskStatus, TaskType
from planloop.core.suggest import SuggestionEngine, TaskSuggestion


@pytest.fixture
def mock_session_state():
    """Create a mock session state."""
    from datetime import datetime

    from planloop.core.state import Environment, Now, NowReason, PromptMetadata

    return SessionState(
        session_id="test-session",
        session="test-session",
        name="Test Session",
        title="Test Project",
        purpose="Testing",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        project_root="/test",
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="test"),
        now=Now(reason=NowReason.IDLE),
        tasks=[
            Task(id=1, title="Existing task", type=TaskType.FEATURE, status=TaskStatus.TODO)
        ]
    )


@pytest.fixture
def mock_context():
    """Create a mock codebase context."""
    context = CodebaseContext(
        project_root=Path("/test"),
        structure={"src": {"main.py": "file", "utils.py": "file"}},
        current_tasks=[],
        recent_changes=["src/main.py"],
        todos=[
            TodoComment(file="src/main.py", line=10, type="TODO", text="Add error handling")
        ],
        language_stats={"py": 10, "md": 2}
    )
    return context


@pytest.fixture
def suggest_config():
    """Create suggestion config."""
    return SuggestConfig(
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        max_suggestions=5
    )


def test_task_suggestion_model():
    """TaskSuggestion should validate correctly."""
    suggestion = TaskSuggestion(
        title="Add error handling to API",
        type=TaskType.FIX,
        priority="high",
        rationale="12 endpoints missing try/catch",
        implementation_notes="See pattern in auth module",
        affected_files=["src/api/routes.py"],
        depends_on=[]
    )

    assert suggestion.title == "Add error handling to API"
    assert suggestion.priority == "high"
    assert len(suggestion.affected_files) == 1


def test_suggestion_engine_initializes(mock_session_state, suggest_config):
    """SuggestionEngine should initialize with session and config."""
    engine = SuggestionEngine(mock_session_state, suggest_config)

    assert engine.session == mock_session_state
    assert engine.config == suggest_config


def test_suggestion_engine_builds_prompt(mock_session_state, mock_context, suggest_config):
    """SuggestionEngine should build a prompt from context."""
    engine = SuggestionEngine(mock_session_state, suggest_config)

    prompt = engine._build_prompt(mock_context)

    # Should include key information
    assert "test-session" in prompt or "session" in prompt.lower()
    assert "TODO" in prompt
    assert "main.py" in prompt
    assert "JSON" in prompt or "json" in prompt.lower()


def test_suggestion_engine_validates_suggestions(mock_session_state, suggest_config):
    """SuggestionEngine should validate suggestion structure."""
    engine = SuggestionEngine(mock_session_state, suggest_config)

    valid = TaskSuggestion(
        title="Valid task",
        type=TaskType.FEATURE,
        priority="medium",
        rationale="Good reason",
        implementation_notes="Clear notes",
        affected_files=["file.py"]
    )

    assert engine._validate_suggestion(valid) is True

    # Invalid: empty title
    invalid = TaskSuggestion(
        title="",
        type=TaskType.FEATURE,
        priority="medium",
        rationale="Reason",
        implementation_notes="Notes",
        affected_files=[]
    )

    assert engine._validate_suggestion(invalid) is False


def test_suggestion_engine_checks_duplicates(mock_session_state, suggest_config):
    """SuggestionEngine should detect duplicate tasks."""
    engine = SuggestionEngine(mock_session_state, suggest_config)

    # Suggestion with similar title to existing task
    duplicate = TaskSuggestion(
        title="Existing task",  # Same as in session
        type=TaskType.FEATURE,
        priority="low",
        rationale="Reason",
        implementation_notes="Notes",
        affected_files=[]
    )

    assert engine._check_duplicates(duplicate) is True

    # Different task
    unique = TaskSuggestion(
        title="Completely new task",
        type=TaskType.FEATURE,
        priority="low",
        rationale="Reason",
        implementation_notes="Notes",
        affected_files=[]
    )

    assert engine._check_duplicates(unique) is False


def test_suggestion_engine_generates_suggestions(mock_session_state, mock_context, suggest_config):
    """SuggestionEngine should generate suggestions via LLM."""
    # Mock LLM response
    mock_llm_response = json.dumps([
        {
            "title": "Add error handling",
            "type": "fix",
            "priority": "high",
            "rationale": "Found TODO comment",
            "implementation_notes": "Add try/catch blocks",
            "affected_files": ["src/main.py"],
            "depends_on": []
        }
    ])

    with patch("planloop.core.suggest.LLMClient") as MockLLM:
        mock_client = Mock()
        mock_client.generate_json.return_value = json.loads(mock_llm_response)
        MockLLM.return_value = mock_client

        engine = SuggestionEngine(mock_session_state, suggest_config)
        suggestions = engine.generate_suggestions(mock_context)

        assert len(suggestions) >= 1
        assert suggestions[0].title == "Add error handling"
        assert suggestions[0].priority == "high"


def test_suggestion_engine_filters_invalid_suggestions(mock_session_state, mock_context, suggest_config):
    """SuggestionEngine should filter out invalid suggestions."""
    # Mock LLM response with some invalid suggestions
    mock_llm_response = json.dumps([
        {
            "title": "Valid task",
            "type": "feature",
            "priority": "medium",
            "rationale": "Good reason",
            "implementation_notes": "Clear notes",
            "affected_files": ["file.py"],
            "depends_on": []
        },
        {
            "title": "",  # Invalid: empty title
            "type": "feature",
            "priority": "low",
            "rationale": "Reason",
            "implementation_notes": "Notes",
            "affected_files": [],
            "depends_on": []
        }
    ])

    with patch("planloop.core.suggest.LLMClient") as MockLLM:
        mock_client = Mock()
        mock_client.generate_json.return_value = json.loads(mock_llm_response)
        MockLLM.return_value = mock_client

        engine = SuggestionEngine(mock_session_state, suggest_config)
        suggestions = engine.generate_suggestions(mock_context)

        # Should only return valid suggestions
        assert len(suggestions) == 1
        assert suggestions[0].title == "Valid task"


def test_suggestion_engine_limits_suggestions(mock_session_state, mock_context, suggest_config):
    """SuggestionEngine should respect max_suggestions config."""
    # Mock LLM response with many suggestions
    mock_suggestions = [
        {
            "title": f"Task {i}",
            "type": "feature",
            "priority": "low",
            "rationale": "Reason",
            "implementation_notes": "Notes",
            "affected_files": [],
            "depends_on": []
        }
        for i in range(10)
    ]

    with patch("planloop.core.suggest.LLMClient") as MockLLM:
        mock_client = Mock()
        mock_client.generate_json.return_value = mock_suggestions
        MockLLM.return_value = mock_client

        config = SuggestConfig(max_suggestions=3)
        engine = SuggestionEngine(mock_session_state, config)
        suggestions = engine.generate_suggestions(mock_context)

        # Should limit to max_suggestions
        assert len(suggestions) <= 3


def test_suggestion_engine_handles_llm_errors(mock_session_state, mock_context, suggest_config):
    """SuggestionEngine should handle LLM errors gracefully."""
    with patch("planloop.core.suggest.LLMClient") as MockLLM:
        mock_client = Mock()
        mock_client.generate_json.side_effect = Exception("LLM API error")
        MockLLM.return_value = mock_client

        engine = SuggestionEngine(mock_session_state, suggest_config)

        # Should raise a meaningful error
        from planloop.core.llm_client import LLMError
        with pytest.raises(LLMError):
            engine.generate_suggestions(mock_context)


def test_suggestion_engine_uses_context_builder(mock_session_state, suggest_config, mock_context):
    """SuggestionEngine should build context if not provided."""
    with patch("planloop.core.suggest.ContextBuilder") as MockBuilder:
        mock_builder = Mock()
        mock_builder.build.return_value = mock_context  # Use real mock_context fixture
        MockBuilder.return_value = mock_builder

        with patch("planloop.core.suggest.LLMClient") as MockLLM:
            mock_client = Mock()
            mock_client.generate_json.return_value = []
            MockLLM.return_value = mock_client

            engine = SuggestionEngine(mock_session_state, suggest_config)

            # Generate with project_root instead of context
            engine.generate_suggestions(
                context=None,
                project_root=Path("/test"),
                depth="shallow"
            )

            # Should have built context
            MockBuilder.assert_called_once()
            mock_builder.build.assert_called_once_with(depth="shallow")
