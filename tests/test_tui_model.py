"""Tests for TUI view model."""
from __future__ import annotations

from datetime import datetime

from planloop.tui.app import SessionViewModel
from planloop.core.state import Environment, Now, NowReason, PromptMetadata, SessionState, Task, TaskType


def fake_state() -> SessionState:
    now = Now(reason=NowReason.TASK, task_id=1)
    env = Environment(os="macOS")
    prompts = PromptMetadata(set="core-v1")
    return SessionState(
        session="demo",
        name="demo",
        title="Demo Session",
        purpose="",
        created_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
        project_root="/repo",
        prompts=prompts,
        environment=env,
        tasks=[Task(id=1, title="Task A", type=TaskType.FEATURE)],
        now=now,
    )


def test_session_view_model():
    state = fake_state()
    model = SessionViewModel.from_state(state)
    assert model.session == "demo"
    assert model.tasks[0][1] == "Task A"
