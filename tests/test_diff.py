"""Tests for state diff helper."""
from __future__ import annotations

from datetime import datetime

from planloop.core.diff import state_diff
from planloop.core.state import Environment, Now, NowReason, PromptMetadata, SessionState, Task, TaskStatus, TaskType


def build_state(tasks):
    return SessionState(
        session="s",
        name="n",
        title="t",
        purpose="p",
        created_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
        project_root="/repo",
        prompts=PromptMetadata(set="core-v1"),
        environment=Environment(os="mac"),
        tasks=tasks,
        now=Now(reason=NowReason.IDLE),
    )


def test_state_diff_detects_added_and_updated_tasks():
    before = build_state([
        Task(id=1, title="One", type=TaskType.FEATURE, status=TaskStatus.TODO),
    ])
    after = build_state([
        Task(id=1, title="One", type=TaskType.FEATURE, status=TaskStatus.DONE),
        Task(id=2, title="Two", type=TaskType.TEST),
    ])

    diff = state_diff(before, after)

    assert diff["tasks"]["added"][0]["id"] == 2
    assert diff["tasks"]["updated"][0]["changes"]["status"]["after"] == "DONE"


def test_state_diff_detects_context_changes():
    before = build_state([])
    after = build_state([])
    before.context_notes = ["old"]
    after.context_notes = ["new"]

    diff = state_diff(before, after)

    assert diff["context_notes"]["before"] == ["old"]
    assert diff["context_notes"]["after"] == ["new"]
