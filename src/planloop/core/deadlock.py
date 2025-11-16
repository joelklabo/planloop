"""Deadlock detection helpers for planloop."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .state import Now, NowReason, SessionState, Signal, SignalLevel, SignalType

DEADLOCK_FILE = "deadlock.json"


@dataclass
class DeadlockTracker:
    last_state_hash: str = ""
    no_progress_counter: int = 0
    queue_head: str | None = None
    queue_stall_counter: int = 0

    def to_json(self) -> str:
        import json

        return json.dumps(self.__dict__)

    @classmethod
    def from_file(cls, path: Path) -> DeadlockTracker:
        if not path.exists():
            return cls()
        import json

        data = json.loads(path.read_text(encoding="utf-8") or "{}")
        return cls(**data)

    def persist(self, path: Path) -> None:
        path.write_text(self.to_json(), encoding="utf-8")


    def register_queue_head(self, head_agent: str | None, should_track: bool, threshold: int) -> bool:
        if not should_track or not head_agent:
            self.queue_head = None
            self.queue_stall_counter = 0
            return False

        if self.queue_head != head_agent:
            self.queue_head = head_agent
            self.queue_stall_counter = 1
        else:
            self.queue_stall_counter += 1

        return self.queue_stall_counter >= threshold


def _compute_hash(state: SessionState) -> str:
    payload = state.model_dump_json(exclude={"last_updated_at"})
    return hashlib.sha256(payload.encode()).hexdigest()


def check_deadlock(state: SessionState, session_dir: Path, threshold: int = 10) -> SessionState:
    tracker_path = session_dir / DEADLOCK_FILE
    tracker = DeadlockTracker.from_file(tracker_path)

    state_hash = _compute_hash(state)
    if state_hash == tracker.last_state_hash:
        tracker.no_progress_counter += 1
    else:
        tracker.last_state_hash = state_hash
        tracker.no_progress_counter = 0

    if tracker.no_progress_counter >= threshold:
        deadlock_signal = Signal(
            id="deadlock",
            type=SignalType.SYSTEM,
            kind="deadlock_suspected",
            level=SignalLevel.BLOCKER,
            title="Potential deadlock detected",
            message="Agent called status without making progress",
        )
        existing = [s for s in state.signals if s.id == deadlock_signal.id]
        if not existing:
            state.signals.append(deadlock_signal)
        state.now = Now(reason=NowReason.DEADLOCKED, signal_id=deadlock_signal.id)

    tracker.persist(tracker_path)
    return state
