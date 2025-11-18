"""Filesystem lock helpers for planloop sessions."""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from ..logging_utils import log_session_event
from .deadlock import DEADLOCK_FILE, DeadlockTracker
from .session import load_session_state_from_disk, save_session_state
from .signals import Signal, open_signal
from .state import Now, NowReason, SignalLevel, SignalType

LOCK_FILE = ".lock"
LOCK_INFO_FILE = ".lock_info"
LOCK_QUEUE_DIR = ".lock_queue"
DEFAULT_TIMEOUT = 30
SLEEP_INTERVAL = 0.1
QUEUE_STALL_THRESHOLD = 5
QUEUE_STALL_SIGNAL_ID = "queue_stall"


@dataclass
class LockInfo:
    held_by: str
    since: float
    operation: str

    def to_dict(self) -> dict:
        return {"held_by": self.held_by, "since": self.since, "operation": self.operation}

    @classmethod
    def from_file(cls, path: Path) -> LockInfo | None:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(**data)
        except json.JSONDecodeError:
            return None




@dataclass
class LockStatus:
    locked: bool
    info: LockInfo | None


@dataclass
class QueueEntry:
    id: str
    agent: str
    operation: str
    requested_at: float

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent": self.agent,
            "operation": self.operation,
            "requested_at": self.requested_at,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> QueueEntry:
        return cls(
            id=raw["id"],
            agent=raw["agent"],
            operation=raw["operation"],
            requested_at=raw["requested_at"],
        )


@dataclass
class LockQueueStatus:
    pending: list[QueueEntry]
    position: int | None

    def to_dict(self) -> dict:
        return {
            "pending": [entry.to_dict() for entry in self.pending],
            "position": self.position,
        }


def _queue_dir(session_dir: Path) -> Path:
    return session_dir / LOCK_QUEUE_DIR


def _queue_entry_path(session_dir: Path, entry_id: str) -> Path:
    return _queue_dir(session_dir) / f"{entry_id}.json"


def _ensure_queue_dir(session_dir: Path) -> None:
    _queue_dir(session_dir).mkdir(parents=True, exist_ok=True)


def _write_queue_entry(session_dir: Path, entry: QueueEntry) -> None:
    _ensure_queue_dir(session_dir)
    path = _queue_entry_path(session_dir, entry.id)
    path.write_text(json.dumps(entry.to_dict()), encoding="utf-8")
    log_session_event(session_dir, f"Queue entry {entry.id} registered for {entry.operation}")


def _remove_queue_entry(session_dir: Path, entry_id: str, log_event: bool = True) -> None:
    path = _queue_entry_path(session_dir, entry_id)
    if not path.exists():
        return
    path.unlink()
    if log_event:
        log_session_event(session_dir, f"Queue entry {entry_id} removed")


def _load_raw_queue_entries(session_dir: Path) -> list[QueueEntry]:
    queue_dir = _queue_dir(session_dir)
    if not queue_dir.exists():
        return []
    entries: list[QueueEntry] = []
    for path in sorted(queue_dir.iterdir()):
        if path.suffix != ".json":
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            entries.append(QueueEntry.from_dict(raw))
        except (json.JSONDecodeError, KeyError, TypeError):
            path.unlink(missing_ok=True)
    return sorted(entries, key=lambda entry: entry.requested_at)


def _prune_stale_entries(session_dir: Path, entries: list[QueueEntry], max_age: float) -> list[QueueEntry]:
    now = time.time()
    keep: list[QueueEntry] = []
    for entry in entries:
        if now - entry.requested_at > max_age:
            _remove_queue_entry(session_dir, entry.id, log_event=True)
        else:
            keep.append(entry)
    return keep


def _load_queue_entries(session_dir: Path, max_age: float) -> list[QueueEntry]:
    entries = _load_raw_queue_entries(session_dir)
    return _prune_stale_entries(session_dir, entries, max_age)


def get_lock_queue_status(session_dir: Path, agent: str | None = None, max_age: float = DEFAULT_TIMEOUT) -> LockQueueStatus:
    entries = _load_queue_entries(session_dir, max_age)
    position: int | None = None
    if agent:
        for idx, entry in enumerate(entries):
            if entry.agent == agent:
                position = idx + 1
                break
    return LockQueueStatus(pending=entries, position=position)


def _emit_queue_stall_signal(session_dir: Path, head_agent: str | None, threshold: int) -> None:
    state = load_session_state_from_disk(session_dir)
    signal_id = QUEUE_STALL_SIGNAL_ID
    if any(sig.id == signal_id and sig.open for sig in state.signals):
        return

    signal = Signal(
        id=signal_id,
        type=SignalType.SYSTEM,
        kind="queue_stall",
        level=SignalLevel.BLOCKER,
        title="Queue stall detected",
        message=f"Agent {head_agent or 'unknown'} held the lock queue for {threshold} consecutive cycles.",
        extra={"queue_head": head_agent, "threshold": threshold},
    )

    try:
        open_signal(state, signal=signal)
    except ValueError:
        return

    state.now = Now(reason=NowReason.WAITING_ON_LOCK, signal_id=signal_id)
    save_session_state(session_dir, state, message="Queue stall detected")


@contextmanager
def acquire_lock(session_dir: Path, operation: str, timeout: int = DEFAULT_TIMEOUT) -> Iterator[None]:
    lock_path = session_dir / LOCK_FILE
    info_path = session_dir / LOCK_INFO_FILE
    start = time.time()
    held_by = f"pid:{os.getpid()}"
    agent = os.environ.get("PLANLOOP_AGENT_NAME", held_by)
    entry_id = str(uuid.uuid4())
    queue_entry = QueueEntry(
        id=entry_id,
        agent=agent,
        operation=operation,
        requested_at=start,
    )
    _write_queue_entry(session_dir, queue_entry)

    # Log lock requested
    try:
        from ..dev_mode.lock_logger import log_lock_event
        log_lock_event(session_dir, "lock_requested", operation, entry_id)
    except ImportError:
        pass  # dev_mode not available

    tracker_path = session_dir / DEADLOCK_FILE
    tracker = DeadlockTracker.from_file(tracker_path)
    queue_stall_detected = False
    queue_stall_head: str | None = None
    lock_acquired_time: float | None = None

    try:
        while True:
            entries = _load_queue_entries(session_dir, timeout)
            head = entries[0] if entries else None
            should_track = bool(head and head.agent != agent and len(entries) > 1)
            if tracker.register_queue_head(head.agent if head else None, should_track, QUEUE_STALL_THRESHOLD):
                queue_stall_detected = True
                queue_stall_head = head.agent if head else None
            tracker.persist(tracker_path)

            if head is None or head.id != entry_id:
                if timeout == 0:
                    raise TimeoutError("Lock already held")
                if time.time() - start > timeout:
                    holder_info = get_lock_status(session_dir).info
                    holder = holder_info.held_by if holder_info else "unknown"
                    log_session_event(
                        session_dir,
                        f"Queue wait timeout for {operation}; held by {holder}",
                        level=logging.WARNING,
                    )
                    raise TimeoutError(f"Timeout waiting for lock held by {holder}")
                time.sleep(SLEEP_INTERVAL)
                continue
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                acquired_time = time.time()
                wait_ms = (acquired_time - start) * 1000
                info = LockInfo(held_by=held_by, since=acquired_time, operation=operation)
                info_path.write_text(json.dumps(info.to_dict()), encoding="utf-8")
                log_session_event(session_dir, f"Lock acquired for {operation}")

                # Log lock acquired with wait time
                try:
                    from ..dev_mode.lock_logger import log_lock_event
                    log_lock_event(session_dir, "lock_acquired", operation, entry_id, wait_ms=wait_ms)
                except ImportError:
                    pass
                break
            except FileExistsError as e:
                if timeout == 0:
                    raise TimeoutError("Lock already held") from e
                if time.time() - start > timeout:
                    lock_info: LockInfo | None = LockInfo.from_file(info_path)
                    holder = lock_info.held_by if lock_info else "unknown"
                    log_session_event(
                        session_dir,
                        f"Lock timeout for {operation}; held by {holder}",
                        level=logging.WARNING,
                    )
                    raise TimeoutError(f"Lock held by {holder} longer than {timeout}s") from e
                time.sleep(SLEEP_INTERVAL)
        if queue_stall_detected:
            _emit_queue_stall_signal(session_dir, queue_stall_head, QUEUE_STALL_THRESHOLD)

        # Track when lock was acquired for hold time calculation
        lock_acquired_time = time.time()
        yield
    finally:
        release_time = time.time()
        hold_ms = (release_time - lock_acquired_time) * 1000 if lock_acquired_time is not None else None

        if lock_path.exists():
            lock_path.unlink()
        if info_path.exists():
            info_path.unlink()

        # Only log release if lock was actually acquired
        if lock_acquired_time is not None:
            log_session_event(session_dir, f"Lock released for {operation}")

            # Log lock released with hold time
            try:
                from ..dev_mode.lock_logger import log_lock_event
                log_lock_event(session_dir, "lock_released", operation, entry_id, hold_ms=hold_ms)
            except ImportError:
                pass

        _remove_queue_entry(session_dir, entry_id)


def get_lock_status(session_dir: Path) -> LockStatus:
    lock_path = session_dir / LOCK_FILE
    info_path = session_dir / LOCK_INFO_FILE
    locked = lock_path.exists()
    info_obj: LockInfo | None = None
    if locked:
        info_obj = LockInfo.from_file(info_path)
    return LockStatus(locked=locked, info=info_obj)
