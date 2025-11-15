"""Tests for planloop state updates."""
from __future__ import annotations

from datetime import datetime

import pytest

from planloop.core.state import Environment, Now, NowReason, PromptMetadata, SessionState, Task, TaskStatus, TaskType
from planloop.core.update import UpdateError, apply_update
from planloop.core.update_payload import AddTaskInput, TaskStatusPatch, UpdatePayload


def make_state() -> SessionState:
    now = Now(reason=NowReason.IDLE)
    env = Environment(os="macOS")
    prompts = PromptMetadata(set="core-v1")
    return SessionState(
        session="abc",
        name="abc",
        title="Demo",
        purpose="Test",
        created_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
        project_root="/repo",
        prompts=prompts,
        environment=env,
        tasks=[Task(id=1, title="Start", type=TaskType.CHORE)],
        now=now,
    )


def test_apply_update_changes_task_status():
    state = make_state()
    payload = UpdatePayload(
        session="abc",
        tasks=[TaskStatusPatch(id=1, status=TaskStatus.IN_PROGRESS)],
    )

    result = apply_update(state, payload)

    assert result.tasks[0].status == TaskStatus.IN_PROGRESS
    assert result.version == 2


def test_apply_update_adds_task():
    state = make_state()
    payload = UpdatePayload(
        session="abc",
        add_tasks=[AddTaskInput(title="New task", type=TaskType.FEATURE)],
    )

    result = apply_update(state, payload)

    assert len(result.tasks) == 2
    assert result.tasks[-1].title == "New task"


def test_apply_update_rejects_version_mismatch():
    state = make_state()
    payload = UpdatePayload(
        session="abc",
        last_seen_version="999",
    )

    with pytest.raises(UpdateError):
        apply_update(state, payload)
