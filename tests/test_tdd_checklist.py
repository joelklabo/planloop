"""Tests for TDD checklist in status output (P1.4).

Verifies that agents receive TDD workflow reminders in status responses
to enforce the test-driven development practice.
"""
import json
from datetime import datetime

from planloop.core.session import save_session_state
from planloop.core.state import (
    Environment,
    Now,
    NowReason,
    PromptMetadata,
    SessionState,
    Task,
    TaskStatus,
    TaskType,
)


def test_status_includes_tdd_checklist_when_task_active(tmp_path, monkeypatch):
    """Status includes TDD checklist when working on a task."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    state = SessionState(
        session="test-tdd-checklist",
        project_root=str(tmp_path),
        name="Test",
        title="TDD Test",
        purpose="Test TDD checklist",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.TASK, task_id=1),
        tasks=[
            Task(
                id=1,
                title="Implement feature",
                type=TaskType.FEATURE,
                status=TaskStatus.IN_PROGRESS,
            ),
        ],
    )

    session_dir = tmp_path / "sessions" / "test-tdd-checklist"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)

    from typer.testing import CliRunner

    from planloop.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--session", "test-tdd-checklist", "--json"])
    assert result.exit_code == 0
    output = json.loads(result.stdout)

    # Should include TDD checklist
    assert "tdd_checklist" in output
    checklist = output["tdd_checklist"]

    # Verify checklist items
    assert isinstance(checklist, list)
    assert len(checklist) >= 5

    # Check for key TDD steps
    checklist_text = " ".join(checklist).lower()
    assert "test" in checklist_text
    assert "fail" in checklist_text or "red" in checklist_text
    assert "implement" in checklist_text
    assert "pass" in checklist_text or "green" in checklist_text
    assert "commit" in checklist_text


def test_status_omits_tdd_checklist_when_no_tasks(tmp_path, monkeypatch):
    """Status omits TDD checklist when no tasks are active."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    state = SessionState(
        session="test-no-tdd",
        project_root=str(tmp_path),
        name="Test",
        title="No TDD Test",
        purpose="Test no checklist",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.IDLE),
        tasks=[],
    )

    session_dir = tmp_path / "sessions" / "test-no-tdd"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)

    from typer.testing import CliRunner

    from planloop.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--session", "test-no-tdd", "--json"])
    assert result.exit_code == 0
    output = json.loads(result.stdout)

    # Should not include TDD checklist when idle
    assert "tdd_checklist" not in output or output["tdd_checklist"] is None


def test_tdd_checklist_is_actionable(tmp_path, monkeypatch):
    """TDD checklist provides clear, actionable steps."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    state = SessionState(
        session="test-actionable-tdd",
        project_root=str(tmp_path),
        name="Test",
        title="Actionable TDD",
        purpose="Test actionable checklist",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.TASK, task_id=1),
        tasks=[
            Task(id=1, title="Task", type=TaskType.FEATURE, status=TaskStatus.TODO),
        ],
    )

    session_dir = tmp_path / "sessions" / "test-actionable-tdd"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)

    from typer.testing import CliRunner

    from planloop.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--session", "test-actionable-tdd", "--json"])
    assert result.exit_code == 0
    output = json.loads(result.stdout)

    checklist = output["tdd_checklist"]

    # Each item should be a clear action
    for item in checklist:
        assert isinstance(item, str)
        assert len(item) > 10  # Should be descriptive
        # Should not be empty or just a number
        assert item.strip() and not item.strip().isdigit()
