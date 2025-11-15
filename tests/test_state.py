"""Basic tests for SessionState models."""
from __future__ import annotations

from datetime import datetime

from planloop.core.state import (
    Artifact,
    ArtifactType,
    Environment,
    Now,
    NowReason,
    PromptMetadata,
    SessionState,
    Signal,
    SignalLevel,
    SignalType,
    Task,
    TaskStatus,
    TaskType,
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
