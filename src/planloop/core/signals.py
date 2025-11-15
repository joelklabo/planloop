"""Signal management helpers."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from .state import SessionState, Signal, SignalLevel, SignalType


def open_signal(state: SessionState, *, signal: Signal) -> None:
    existing = [s for s in state.signals if s.id == signal.id]
    if existing:
        raise ValueError(f"Signal {signal.id} already exists")
    state.signals.append(signal)
    state.last_updated_at = datetime.utcnow()
    state.now = state.compute_now()


def close_signal(state: SessionState, signal_id: str) -> None:
    target = None
    for sig in state.signals:
        if sig.id == signal_id:
            target = sig
            break
    if not target:
        raise ValueError(f"Signal {signal_id} not found")
    target.open = False
    state.last_updated_at = datetime.utcnow()
    state.now = state.compute_now()
