"""Tests for suggest hints in planloop status command."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from planloop import cli
from planloop.core.session import create_session
from planloop.core.state import Task, TaskStatus, TaskType

runner = CliRunner()


def test_status_suggests_discover_when_no_tasks(monkeypatch, tmp_path):
    """Status should suggest running planloop suggest when no tasks exist."""
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "title", project_root=Path("/repo"))
    
    # State has no tasks
    assert len(state.tasks) == 0
    
    result = runner.invoke(cli.app, ["status", "--session", state.session])
    assert result.exit_code == 0
    
    data = json.loads(result.stdout)
    assert "agent_instructions" in data
    assert "planloop suggest" in data["agent_instructions"]
    assert data["now"]["reason"] == "idle"


def test_status_suggests_discover_when_all_tasks_done(monkeypatch, tmp_path):
    """Status should suggest running planloop suggest when all tasks are complete."""
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "title", project_root=Path("/repo"))
    
    # Add a completed task
    task = Task(
        id=1,
        title="Test task",
        type=TaskType.FEATURE,
        status=TaskStatus.DONE
    )
    state.tasks.append(task)
    
    # Recompute now field
    state.now = state.compute_now()
    
    # Save state
    from planloop.core.session import save_session_state
    from planloop.home import SESSIONS_DIR
    session_dir = home / SESSIONS_DIR / state.session
    save_session_state(session_dir, state)
    
    result = runner.invoke(cli.app, ["status", "--session", state.session])
    assert result.exit_code == 0
    
    data = json.loads(result.stdout)
    assert "agent_instructions" in data
    assert "planloop suggest" in data["agent_instructions"]
    assert data["now"]["reason"] == "completed"


def test_status_does_not_suggest_when_tasks_in_progress(monkeypatch, tmp_path):
    """Status should not suggest planloop suggest when tasks are in progress."""
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "title", project_root=Path("/repo"))
    
    # Add a task in progress
    task = Task(
        id=1,
        title="Test task",
        type=TaskType.FEATURE,
        status=TaskStatus.IN_PROGRESS
    )
    state.tasks.append(task)
    
    # Recompute now field
    state.now = state.compute_now()
    
    # Save state
    from planloop.core.session import save_session_state
    from planloop.home import SESSIONS_DIR
    session_dir = home / SESSIONS_DIR / state.session
    save_session_state(session_dir, state)
    
    result = runner.invoke(cli.app, ["status", "--session", state.session])
    assert result.exit_code == 0
    
    data = json.loads(result.stdout)
    assert "agent_instructions" in data
    # Should not mention suggest when there's work to do
    assert "planloop suggest" not in data["agent_instructions"]
    assert data["now"]["reason"] == "task"
