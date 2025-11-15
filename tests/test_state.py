"""Basic tests for SessionState models."""
from __future__ import annotations

from datetime import datetime

import pytest

from planloop.core.state import (
    Artifact,
    ArtifactType,
    Environment,
    Now,
    NowReason,
    PromptMetadata,
    SessionState,
    StateValidationError,
    Signal,
    SignalLevel,
    SignalType,
    Task,
    TaskStatus,
    TaskType,
    validate_state,
)


def minimal_state() -> SessionState:
    now = Now(reason=NowReason.IDLE)
    env = Environment(os="macOS", python="3.11.0")
    prompts = PromptMetadata(set="core-v1")
    return SessionState(
        session="test-session",
        name="test",
        title="Test Session",
        purpose="Run tests",
        created_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
        project_root="/tmp/project",
        prompts=prompts,
        environment=env,
        now=now,
    )


def test_session_state_defaults():
    state = minimal_state()

    assert state.tasks == []
    assert state.signals == []
    assert state.next_steps == []
    assert state.context_notes == []
    assert state.artifacts == []
    assert state.done is False
    assert state.final_summary is None


def test_task_model_round_trip():
    task = Task(id=1, title="Write tests", type=TaskType.TEST)
    assert task.status == TaskStatus.TODO


def test_signal_model_defaults():
    signal = Signal(
        id="ci-1",
        type=SignalType.CI,
        kind="build_failed",
        level=SignalLevel.BLOCKER,
        title="CI failed",
        message="Tests failed",
    )
    assert signal.open is True
    assert signal.extra == {}


def test_artifact_model():
    artifact = Artifact(type=ArtifactType.DIFF, summary="diff text")
    assert artifact.metadata == {}


def test_compute_now_prefers_blockers():
    state = minimal_state()
    state.signals.append(
        Signal(
            id="ci-1",
            type=SignalType.CI,
            kind="build_failed",
            level=SignalLevel.BLOCKER,
            title="CI failed",
            message="Tests failing",
        )
    )

    result = state.compute_now()

    assert result.reason == NowReason.CI_BLOCKER
    assert result.signal_id == "ci-1"


def test_compute_now_picks_in_progress_task():
    state = minimal_state()
    state.tasks = [
        Task(id=1, title="Work", type=TaskType.FEATURE, status=TaskStatus.IN_PROGRESS)
    ]

    result = state.compute_now()

    assert result.reason == NowReason.TASK
    assert result.task_id == 1


def test_compute_now_picks_ready_todo():
    state = minimal_state()
    state.tasks = [
        Task(id=1, title="Prep", type=TaskType.CHORE, status=TaskStatus.DONE),
        Task(id=2, title="Implement", type=TaskType.FEATURE, depends_on=[1]),
    ]

    result = state.compute_now()

    assert result.reason == NowReason.TASK
    assert result.task_id == 2


def test_compute_now_reports_completed_when_all_done():
    state = minimal_state()
    state.tasks = [
        Task(id=1, title="Done", type=TaskType.CHORE, status=TaskStatus.DONE)
    ]

    result = state.compute_now()

    assert result.reason == NowReason.COMPLETED


def test_compute_now_idle_when_no_ready_tasks():
    state = minimal_state()
    state.tasks = [
        Task(id=1, title="Blocked", type=TaskType.FEATURE, depends_on=[2]),
        Task(id=2, title="Missing", type=TaskType.FEATURE, status=TaskStatus.BLOCKED),
    ]

    result = state.compute_now()

    assert result.reason == NowReason.IDLE


def test_validate_state_duplicate_ids():
    state = minimal_state()
    state.tasks = [
        Task(id=1, title="One", type=TaskType.CHORE),
        Task(id=1, title="Dup", type=TaskType.CHORE),
    ]
    state.now = state.compute_now()

    with pytest.raises(StateValidationError):
        validate_state(state)


def test_validate_state_missing_dependency():
    state = minimal_state()
    state.tasks = [Task(id=1, title="One", type=TaskType.FEATURE, depends_on=[99])]
    state.now = state.compute_now()

    with pytest.raises(StateValidationError):
        validate_state(state)


def test_validate_state_detects_cycle():
    state = minimal_state()
    state.tasks = [
        Task(id=1, title="A", type=TaskType.FEATURE, depends_on=[2]),
        Task(id=2, title="B", type=TaskType.FEATURE, depends_on=[1]),
    ]
    state.now = state.compute_now()

    with pytest.raises(StateValidationError):
        validate_state(state)


def test_validate_state_now_mismatch():
    state = minimal_state()
    state.tasks = [Task(id=1, title="Work", type=TaskType.CHORE, status=TaskStatus.IN_PROGRESS)]
    state.now = Now(reason=NowReason.IDLE)

    with pytest.raises(StateValidationError):
        validate_state(state)
