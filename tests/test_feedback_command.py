"""Tests for agent feedback collection system (Task 5).

Verifies that agents can provide feedback after session completion,
enabling continuous improvement through learning from experiences.
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


def test_feedback_command_stores_feedback(tmp_path, monkeypatch):
    """Feedback command stores agent feedback in session directory."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    state = SessionState(
        session="test-feedback",
        project_root=str(tmp_path),
        name="Test",
        title="Feedback Test",
        purpose="Test feedback",
        created_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.COMPLETED),
        tasks=[Task(id=1, title="Task", type=TaskType.FEATURE, status=TaskStatus.DONE)],
    )

    session_dir = tmp_path / "sessions" / "test-feedback"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)

    from typer.testing import CliRunner

    from planloop.cli import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "feedback",
            "--session",
            "test-feedback",
            "--message",
            "The status command was confusing at first but TDD workflow helped.",
        ],
    )

    assert result.exit_code == 0

    # Check feedback.json was created
    feedback_path = session_dir / "feedback.json"
    assert feedback_path.exists()

    feedback = json.loads(feedback_path.read_text())
    assert feedback["message"] == "The status command was confusing at first but TDD workflow helped."
    assert "timestamp" in feedback
    assert "agent" in feedback


def test_feedback_with_rating(tmp_path, monkeypatch):
    """Feedback can include optional rating."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    state = SessionState(
        session="test-rating",
        project_root=str(tmp_path),
        name="Test",
        title="Rating Test",
        purpose="Test rating",
        created_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.COMPLETED),
        tasks=[],
    )

    session_dir = tmp_path / "sessions" / "test-rating"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)

    from typer.testing import CliRunner

    from planloop.cli import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "feedback",
            "--session",
            "test-rating",
            "--message",
            "Great experience overall",
            "--rating",
            "4",
        ],
    )

    assert result.exit_code == 0

    feedback_path = session_dir / "feedback.json"
    feedback = json.loads(feedback_path.read_text())
    assert feedback["rating"] == 4


def test_status_prompts_feedback_when_all_done(tmp_path, monkeypatch):
    """Status prompts for feedback when all tasks are complete."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    state = SessionState(
        session="test-prompt",
        project_root=str(tmp_path),
        name="Test",
        title="Prompt Test",
        purpose="Test feedback prompt",
        created_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.COMPLETED),
        tasks=[
            Task(id=1, title="Task 1", type=TaskType.FEATURE, status=TaskStatus.DONE),
            Task(id=2, title="Task 2", type=TaskType.FEATURE, status=TaskStatus.DONE),
        ],
    )

    session_dir = tmp_path / "sessions" / "test-prompt"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)

    from typer.testing import CliRunner

    from planloop.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--session", "test-prompt", "--json"])

    assert result.exit_code == 0
    output = json.loads(result.stdout)

    # Should include feedback prompt
    assert "feedback_request" in output
    feedback_req = output["feedback_request"]

    assert feedback_req is not None
    assert "prompt" in feedback_req
    assert "difficult" in feedback_req["prompt"].lower() or "friction" in feedback_req["prompt"].lower()


def test_feedback_not_prompted_when_tasks_remain(tmp_path, monkeypatch):
    """Feedback not prompted when tasks still TODO."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    state = SessionState(
        session="test-no-prompt",
        project_root=str(tmp_path),
        name="Test",
        title="No Prompt Test",
        purpose="Test no feedback prompt",
        created_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.TASK, task_id=2),
        tasks=[
            Task(id=1, title="Task 1", type=TaskType.FEATURE, status=TaskStatus.DONE),
            Task(id=2, title="Task 2", type=TaskType.FEATURE, status=TaskStatus.TODO),
        ],
    )

    session_dir = tmp_path / "sessions" / "test-no-prompt"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)

    from typer.testing import CliRunner

    from planloop.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--session", "test-no-prompt", "--json"])

    assert result.exit_code == 0
    output = json.loads(result.stdout)

    # Should NOT include feedback prompt
    assert output.get("feedback_request") is None


def test_feedback_includes_session_metadata(tmp_path, monkeypatch):
    """Feedback automatically includes session context."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    state = SessionState(
        session="test-metadata",
        project_root=str(tmp_path),
        name="Test",
        title="Metadata Test",
        purpose="Test metadata",
        created_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.COMPLETED),
        tasks=[
            Task(id=1, title="Task", type=TaskType.FEATURE, status=TaskStatus.DONE)
        ],
    )

    session_dir = tmp_path / "sessions" / "test-metadata"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)

    from typer.testing import CliRunner

    from planloop.cli import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "feedback",
            "--session",
            "test-metadata",
            "--message",
            "Good session",
        ],
    )

    assert result.exit_code == 0

    feedback_path = session_dir / "feedback.json"
    feedback = json.loads(feedback_path.read_text())

    # Should include session context
    assert "session_id" in feedback
    assert feedback["session_id"] == "test-metadata"
    assert "tasks_completed" in feedback
    assert feedback["tasks_completed"] == 1
