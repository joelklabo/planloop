"""Tests for agent continuation mechanism (P1.1, P1.2).

Verifies that agents receive proper guidance to continue working
after completing a task without waiting for user direction.
"""
import json
from pathlib import Path

import pytest

from planloop.core.session import save_session_state
from planloop.core.state import SessionState, Task, TaskStatus


def test_status_suggests_next_task_after_completion(tmp_path, monkeypatch):
    """When a task is completed, status should suggest the next TODO task."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    from datetime import datetime
    from planloop.core.state import Environment, Now, NowReason, PromptMetadata, TaskType

    # Create session with multiple tasks - T1 is done, should suggest T2
    state = SessionState(
        session="test-continuation",
        project_root=str(tmp_path),
        name="Test",
        title="Test Continuation",
        purpose="Test continuation",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.TASK, task_id=2),  # Points to next TODO task
        tasks=[
            Task(id=1, title="First task", type=TaskType.FEATURE, status=TaskStatus.DONE),
            Task(id=2, title="Second task", type=TaskType.FEATURE, status=TaskStatus.TODO),
            Task(id=3, title="Third task", type=TaskType.FEATURE, status=TaskStatus.TODO),
        ],
    )
    
    session_dir = tmp_path / "sessions" / "test-continuation"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)
    
    # Run status command
    from planloop.cli import status
    from typer.testing import CliRunner
    from planloop.cli import app
    
    runner = CliRunner()
    result = runner.invoke(app, ["status", "--session", "test-continuation", "--json"])
    
    assert result.exit_code == 0
    output = json.loads(result.stdout)
    
    # Should include next_action field
    assert "next_action" in output
    next_action = output["next_action"]
    
    # Should suggest working on T2
    assert next_action["action"] == "continue"
    assert next_action["task_id"] == 2
    assert "2" in next_action["message"]
    assert "Second task" in next_action["message"]


def test_status_suggests_planloop_suggest_when_all_done(tmp_path, monkeypatch):
    """When all tasks are done, status should suggest running planloop suggest."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    from datetime import datetime
    from planloop.core.state import Environment, Now, NowReason, PromptMetadata, TaskType

    state = SessionState(
        session="test-all-done",
        project_root=str(tmp_path),
        name="Test",
        title="All Done",
        purpose="Test all done",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.COMPLETED),
        tasks=[
            Task(id=1, title="First task", type=TaskType.FEATURE, status=TaskStatus.DONE),
            Task(id=2, title="Second task", type=TaskType.FEATURE, status=TaskStatus.DONE),
        ],
    )
    
    session_dir = tmp_path / "sessions" / "test-all-done"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)
    
    from typer.testing import CliRunner
    from planloop.cli import app
    
    runner = CliRunner()
    result = runner.invoke(app, ["status", "--session", "test-all-done", "--json"])
    
    assert result.exit_code == 0
    output = json.loads(result.stdout)
    
    assert "next_action" in output
    next_action = output["next_action"]
    
    assert next_action["action"] == "discover"
    assert "suggest" in next_action["message"].lower()


def test_status_no_next_action_when_signal_blocking(tmp_path, monkeypatch):
    """When a signal is blocking, next_action should reflect that."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    from datetime import datetime
    from planloop.core.state import (
        Environment,
        Now,
        NowReason,
        PromptMetadata,
        Signal,
        SignalLevel,
        SignalType,
        TaskType,
    )

    state = SessionState(
        session="test-blocked",
        project_root=str(tmp_path),
        name="Test",
        title="Blocked",
        purpose="Test blocking",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.CI_BLOCKER, signal_id="S1"),
        tasks=[
            Task(id=1, title="First task", type=TaskType.FEATURE, status=TaskStatus.TODO),
        ],
        signals=[
            Signal(
                id="S1",
                type=SignalType.CI,
                kind="build",
                level=SignalLevel.BLOCKER,
                title="Build failed",
                message="Build failed",
            )
        ],
    )
    
    session_dir = tmp_path / "sessions" / "test-blocked"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)
    
    from typer.testing import CliRunner
    from planloop.cli import app
    
    runner = CliRunner()
    result = runner.invoke(app, ["status", "--session", "test-blocked", "--json"])
    
    assert result.exit_code == 0
    output = json.loads(result.stdout)
    
    assert "next_action" in output
    next_action = output["next_action"]
    
    assert next_action["action"] == "fix_blocker"
    assert "S1" in next_action.get("signal_id", "")


def test_status_includes_next_action_always(tmp_path, monkeypatch):
    """Status always includes next_action field for agent guidance."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    from datetime import datetime
    from planloop.core.state import Environment, Now, NowReason, PromptMetadata, TaskType

    # Test with task in progress - should suggest continuing
    state = SessionState(
        session="test-next-action",
        project_root=str(tmp_path),
        name="Test",
        title="Next Action Test",
        purpose="Test next action",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.TASK, task_id=1),
        tasks=[
            Task(id=1, title="Current task", type=TaskType.FEATURE, status=TaskStatus.IN_PROGRESS),
            Task(id=2, title="Next task", type=TaskType.FEATURE, status=TaskStatus.TODO),
        ],
    )
    
    session_dir = tmp_path / "sessions" / "test-next-action"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)

    from typer.testing import CliRunner
    from planloop.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--session", "test-next-action", "--json"])

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    
    # Should always include next_action
    assert "next_action" in output
    next_action = output["next_action"]
    assert next_action["action"] == "continue"
    # next_action suggests next TODO task (task 2), not current IN_PROGRESS (task 1)
    assert next_action["task_id"] == 2
