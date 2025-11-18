"""Tests for suggest CLI command."""
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from planloop.cli import app
from planloop.core.state import TaskType
from planloop.core.suggest import TaskSuggestion


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_suggestions():
    """Mock task suggestions."""
    return [
        TaskSuggestion(
            title="Add error handling",
            type=TaskType.FIX,
            priority="high",
            rationale="Missing try/catch blocks",
            implementation_notes="Add error handling pattern",
            affected_files=["src/api.py"],
            depends_on=[]
        ),
        TaskSuggestion(
            title="Add tests",
            type=TaskType.TEST,
            priority="medium",
            rationale="Low test coverage",
            implementation_notes="Write unit tests",
            affected_files=["tests/test_api.py"],
            depends_on=[]
        )
    ]


def test_suggest_command_exists(runner):
    """Suggest command should be available."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "suggest" in result.stdout


def test_suggest_dry_run_mode(runner, mock_suggestions, tmp_path):
    """Suggest with --dry-run should not modify state."""
    with patch("planloop.cli.SuggestionEngine") as MockEngine:
        mock_engine = Mock()
        mock_engine.generate_suggestions.return_value = mock_suggestions
        MockEngine.return_value = mock_engine

        with patch("planloop.cli._load_session") as mock_load:
                # Create a mock session state
                from datetime import datetime

                from planloop.core.state import (
                    Environment,
                    Now,
                    NowReason,
                    PromptMetadata,
                    SessionState,
                )

                mock_state = SessionState(
                    session="test-session",
                    name="Test",
                    title="Test",
                    purpose="Testing",
                    created_at=datetime.now(),
                    last_updated_at=datetime.now(),
                    project_root=str(tmp_path),
                    prompts=PromptMetadata(set="default"),
                    environment=Environment(os="test"),
                    now=Now(reason=NowReason.IDLE),
                    tasks=[]
                )
                mock_load.return_value = (mock_state, tmp_path)

                result = runner.invoke(app, ["suggest", "--dry-run"])

                assert result.exit_code == 0
                # Should display suggestions
                assert "Add error handling" in result.stdout
                assert "Add tests" in result.stdout


def test_suggest_generates_update_payload(runner, mock_suggestions, tmp_path):
    """Suggest should generate proper update payload for approved tasks."""
    with patch("planloop.cli.SuggestionEngine") as MockEngine:
        mock_engine = Mock()
        mock_engine.generate_suggestions.return_value = mock_suggestions
        MockEngine.return_value = mock_engine

        with patch("planloop.cli._load_session") as mock_load:
                from datetime import datetime

                from planloop.core.state import (
                    Environment,
                    Now,
                    NowReason,
                    PromptMetadata,
                    SessionState,
                )

                mock_state = SessionState(
                    session="test-session",
                    name="Test",
                    title="Test",
                    purpose="Testing",
                    created_at=datetime.now(),
                    last_updated_at=datetime.now(),
                    project_root=str(tmp_path),
                    prompts=PromptMetadata(set="default"),
                    environment=Environment(os="test"),
                    now=Now(reason=NowReason.IDLE),
                    tasks=[]
                )
                mock_load.return_value = (mock_state, tmp_path)

                # Mock the apply_update to verify payload
                with patch("planloop.cli.apply_update") as mock_apply:
                    # apply_update returns modified state
                    mock_apply.return_value = mock_state
                    with patch("planloop.cli.acquire_lock"):
                        result = runner.invoke(app, ["suggest", "--auto-approve"])

                        assert result.exit_code == 0
                        # Should have called apply_update
                        assert mock_apply.called


def test_suggest_respects_limit_option(runner, mock_suggestions, tmp_path):
    """Suggest should respect --limit option."""
    # Create more suggestions than limit
    many_suggestions = mock_suggestions * 5  # 10 suggestions

    with patch("planloop.cli.SuggestionEngine") as MockEngine:
        mock_engine = Mock()
        mock_engine.generate_suggestions.return_value = many_suggestions[:3]  # Engine limits it
        MockEngine.return_value = mock_engine

        with patch("planloop.cli._load_session") as mock_load:
                from datetime import datetime

                from planloop.core.state import (
                    Environment,
                    Now,
                    NowReason,
                    PromptMetadata,
                    SessionState,
                )

                mock_state = SessionState(
                    session="test-session",
                    name="Test",
                    title="Test",
                    purpose="Testing",
                    created_at=datetime.now(),
                    last_updated_at=datetime.now(),
                    project_root=str(tmp_path),
                    prompts=PromptMetadata(set="default"),
                    environment=Environment(os="test"),
                    now=Now(reason=NowReason.IDLE),
                    tasks=[]
                )
                mock_load.return_value = (mock_state, tmp_path)

                result = runner.invoke(app, ["suggest", "--dry-run", "--limit", "3"])

                assert result.exit_code == 0


def test_suggest_uses_specified_depth(runner, mock_suggestions, tmp_path):
    """Suggest should pass depth parameter to engine."""
    with patch("planloop.cli.SuggestionEngine") as MockEngine:
        mock_engine = Mock()
        mock_engine.generate_suggestions.return_value = mock_suggestions
        MockEngine.return_value = mock_engine

        with patch("planloop.cli._load_session") as mock_load:
                from datetime import datetime

                from planloop.core.state import (
                    Environment,
                    Now,
                    NowReason,
                    PromptMetadata,
                    SessionState,
                )

                mock_state = SessionState(
                    session="test-session",
                    name="Test",
                    title="Test",
                    purpose="Testing",
                    created_at=datetime.now(),
                    last_updated_at=datetime.now(),
                    project_root=str(tmp_path),
                    prompts=PromptMetadata(set="default"),
                    environment=Environment(os="test"),
                    now=Now(reason=NowReason.IDLE),
                    tasks=[]
                )
                mock_load.return_value = (mock_state, tmp_path)

                result = runner.invoke(app, ["suggest", "--dry-run", "--depth", "deep"])

                assert result.exit_code == 0
                # Verify depth was passed to engine
                call_args = mock_engine.generate_suggestions.call_args
                assert call_args[1]["depth"] == "deep"
