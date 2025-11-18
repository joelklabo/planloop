"""Tests for task transition detection (P1.2).

Verifies that status correctly detects when a task transitions
from IN_PROGRESS to DONE, enabling autonomous agent continuation.
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


def test_transition_detected_when_task_just_completed(tmp_path, monkeypatch):
    """Status detects transition when a task moves from IN_PROGRESS to DONE."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    # Create session with task 1 IN_PROGRESS, now pointing to it
    state = SessionState(
        session="test-transition",
        project_root=str(tmp_path),
        name="Test",
        title="Transition Test",
        purpose="Test transition detection",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.TASK, task_id=1),
        tasks=[
            Task(
                id=1,
                title="First task",
                type=TaskType.FEATURE,
                status=TaskStatus.IN_PROGRESS,
            ),
            Task(id=2, title="Second task", type=TaskType.FEATURE, status=TaskStatus.TODO),
        ],
    )

    session_dir = tmp_path / "sessions" / "test-transition"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)

    from typer.testing import CliRunner

    from planloop.cli import app

    runner = CliRunner()

    # First call - task 1 still IN_PROGRESS
    result = runner.invoke(app, ["status", "--session", "test-transition", "--json"])
    assert result.exit_code == 0
    output1 = json.loads(result.stdout)
    assert output1["transition_detected"] is False
    assert output1["completed_task_id"] is None

    # Update task 1 to DONE
    update_payload = {
        "session": "test-transition",
        "update_tasks": [{"id": 1, "status": "DONE"}],
    }
    (tmp_path / "update.json").write_text(json.dumps(update_payload))
    result = runner.invoke(
        app, ["update", "--session", "test-transition", "--file", str(tmp_path / "update.json")]
    )
    assert result.exit_code == 0

    # Second call - task 1 now DONE, should detect transition
    result = runner.invoke(app, ["status", "--session", "test-transition", "--json"])
    assert result.exit_code == 0
    output2 = json.loads(result.stdout)

    # Should detect the transition
    assert output2["transition_detected"] is True
    assert output2["completed_task_id"] == 1

    # Should suggest continuing with task 2
    assert output2["next_action"]["action"] == "continue"
    assert output2["next_action"]["task_id"] == 2


def test_no_transition_when_task_was_already_done(tmp_path, monkeypatch):
    """No transition detected if task was already DONE in previous call."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    # Create session with task 1 already DONE
    state = SessionState(
        session="test-no-transition",
        project_root=str(tmp_path),
        name="Test",
        title="No Transition Test",
        purpose="Test no false transitions",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.TASK, task_id=2),
        tasks=[
            Task(id=1, title="First task", type=TaskType.FEATURE, status=TaskStatus.DONE),
            Task(id=2, title="Second task", type=TaskType.FEATURE, status=TaskStatus.TODO),
        ],
    )

    session_dir = tmp_path / "sessions" / "test-no-transition"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)

    from typer.testing import CliRunner

    from planloop.cli import app

    runner = CliRunner()

    # Call status - task 1 was already done
    result = runner.invoke(app, ["status", "--session", "test-no-transition", "--json"])
    assert result.exit_code == 0
    output = json.loads(result.stdout)

    # Should NOT detect transition (task was already done)
    assert output["transition_detected"] is False
    assert output["completed_task_id"] is None


def test_transition_requires_state_tracking(tmp_path, monkeypatch):
    """Transition detection uses last_updated_at timestamp."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    # Implementation uses task.last_updated_at to detect recent completions
    # Tasks completed within last 5 seconds are considered "just completed"

    from datetime import datetime as dt

    state = SessionState(
        session="test-state-tracking",
        project_root=str(tmp_path),
        name="Test",
        title="State Tracking Test",
        purpose="Test state tracking",
        created_at=dt.utcnow(),
        last_updated_at=dt.utcnow(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.COMPLETED),  # Fixed: all tasks done
        tasks=[
            Task(
                id=1,
                title="Task",
                type=TaskType.FEATURE,
                status=TaskStatus.DONE,
                last_updated_at=dt.utcnow(),  # Just completed
            ),
        ],
    )

    session_dir = tmp_path / "sessions" / "test-state-tracking"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)

    from typer.testing import CliRunner

    from planloop.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--session", "test-state-tracking", "--json"])
    assert result.exit_code == 0
    output = json.loads(result.stdout)

    # Should detect transition because task was updated recently
    assert output["transition_detected"] is True
    assert output["completed_task_id"] == 1
