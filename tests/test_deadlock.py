"""Tests for deadlock detection."""
from __future__ import annotations

from pathlib import Path

from planloop.core.deadlock import DeadlockTracker, check_deadlock
from planloop.core.session import create_session
from planloop.core.state import NowReason


def create_state(tmp_path: Path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "Deadlock", project_root=Path("/repo"))
    session_dir = home / "sessions" / state.session
    return state, session_dir


def test_deadlock_tracker_counts(tmp_path, monkeypatch):
    state, session_dir = create_state(tmp_path, monkeypatch)

    for _ in range(5):
        state = check_deadlock(state, session_dir, threshold=3)

    assert state.now.reason == NowReason.DEADLOCKED
    assert (session_dir / "deadlock.json").exists()


def test_register_queue_head_counts():
    tracker = DeadlockTracker()
    assert tracker.register_queue_head("agent-a", should_track=True, threshold=2) is False
    assert tracker.queue_stall_counter == 1
    assert tracker.register_queue_head("agent-a", should_track=True, threshold=2) is True
    assert tracker.queue_stall_counter == 2
    assert tracker.register_queue_head("agent-b", should_track=True, threshold=2) is False
    assert tracker.queue_stall_counter == 1
    assert tracker.register_queue_head(None, should_track=False, threshold=2) is False
    assert tracker.queue_stall_counter == 0
