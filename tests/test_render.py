"""Tests for PLAN.md rendering."""
from __future__ import annotations

from datetime import datetime

from planloop.core.render import parse_front_matter, render_plan
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


def build_state() -> SessionState:
    now = Now(reason=NowReason.TASK, task_id=1)
    env = Environment(os="macOS", python="3.11.0")
    prompts = PromptMetadata(set="core-v1")
    timestamp = datetime(2025, 1, 1, 12, 0, 0)
    return SessionState(
        session="abc-123",
        name="demo",
        title="Demo Plan",
        purpose="Test rendering",
        created_at=timestamp,
        last_updated_at=timestamp,
        project_root="/repo",
        prompts=prompts,
        environment=env,
        tasks=[
            Task(
                id=1,
                title="Bootstrap",
                type=TaskType.CHORE,
                status=TaskStatus.IN_PROGRESS,
                depends_on=[],
            )
        ],
        signals=[
            Signal(
                id="ci-1",
                type=SignalType.CI,
                kind="build",
                level=SignalLevel.BLOCKER,
                title="CI failing",
                message="Tests failing",
            )
        ],
        context_notes=["Remember to update docs"],
        next_steps=["Finish renderer"],
        artifacts=[
            Artifact(
                type=ArtifactType.LOG,
                summary="pytest output",
                path="logs/pytest.txt",
            )
        ],
        now=now,
    )


def test_render_plan_contains_sections():
    state = build_state()
    text = render_plan(state)

    assert text.startswith("---\n")
    assert "planloop_version:" in text.splitlines()[1]
    assert "# Plan: Demo Plan" in text
    assert "## Tasks" in text
    assert "Bootstrap" in text
    assert "## Signals (Snapshot)" in text


def test_parse_front_matter_round_trip():
    state = build_state()
    text = render_plan(state)

    front, body = parse_front_matter(text)

    assert front["session"] == state.session
    assert front["prompt_set"] == state.prompts.set
    assert "# Plan: Demo Plan" in body
