"""Lock operation logging for observability."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from .observability import get_current_trace_id


def log_lock_event(
    session_dir: Path,
    event: str,
    operation: str,
    entry_id: str,
    wait_ms: float | None = None,
    hold_ms: float | None = None,
) -> None:
    """Log a lock-related event to planloop.jsonl.

    Args:
        session_dir: Path to session directory
        event: Event type (lock_requested, lock_acquired, lock_released)
        operation: Operation name (e.g., "update", "suggest")
        entry_id: Queue entry ID
        wait_ms: Wait time in milliseconds (for acquired events)
        hold_ms: Hold time in milliseconds (for released events)
    """
    from typing import Any

    trace_id = get_current_trace_id()
    timestamp = datetime.now(UTC).isoformat()

    log_entry: dict[str, Any] = {
        "timestamp": timestamp,
        "event": event,
        "trace_id": trace_id,
        "operation": operation,
        "lock_entry_id": entry_id,
    }

    if wait_ms is not None:
        log_entry["wait_ms"] = wait_ms

    if hold_ms is not None:
        log_entry["hold_ms"] = hold_ms

    # Write to planloop.jsonl
    log_dir = session_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "planloop.jsonl"

    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


__all__ = ["log_lock_event"]
