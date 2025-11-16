"""Tests for session lock helpers."""
from __future__ import annotations

import json
import threading
import time

import pytest

from planloop.core.lock import (
    LOCK_FILE,
    LOCK_QUEUE_DIR,
    acquire_lock,
    get_lock_queue_status,
    get_lock_status,
)


def test_acquire_lock_creates_lock(tmp_path):
    session_dir = tmp_path

    with acquire_lock(session_dir, operation="write"):
        assert (session_dir / LOCK_FILE).exists()

    assert not (session_dir / LOCK_FILE).exists()


def test_acquire_lock_times_out(tmp_path):
    session_dir = tmp_path

    with acquire_lock(session_dir, operation="one"):
        with pytest.raises(TimeoutError):
            with acquire_lock(session_dir, operation="two", timeout=0):
                pass


def test_acquire_lock_blocks_until_release(tmp_path):
    session_dir = tmp_path
    order = []

    def hold_lock():
        with acquire_lock(session_dir, operation="holder", timeout=5):
            order.append("holder")
            time.sleep(0.2)

    t = threading.Thread(target=hold_lock)
    t.start()
    time.sleep(0.05)

    with acquire_lock(session_dir, operation="waiter", timeout=5):
        order.append("waiter")

    t.join()
    assert order == ["holder", "waiter"]


def test_get_lock_status(tmp_path):
    session_dir = tmp_path
    status = get_lock_status(session_dir)
    assert status.locked is False
    assert status.info is None

    with acquire_lock(session_dir, operation="write"):
        status = get_lock_status(session_dir)
        assert status.locked is True
        assert status.info is not None
        assert status.info.operation == "write"


def test_acquire_lock_registers_queue_entry(tmp_path):
    session_dir = tmp_path
    queue_dir = session_dir / LOCK_QUEUE_DIR

    with acquire_lock(session_dir, operation="write"):
        entries = list(queue_dir.glob("*.json"))
        assert len(entries) == 1
        data = json.loads(entries[0].read_text(encoding="utf-8"))
        assert data["operation"] == "write"

    assert not queue_dir.exists() or not any(queue_dir.iterdir())


def test_get_lock_queue_status_prunes_stale(tmp_path):
    session_dir = tmp_path
    queue_dir = session_dir / LOCK_QUEUE_DIR
    queue_dir.mkdir()
    stale = queue_dir / "stale.json"
    stale.write_text(
        json.dumps(
            {
                "id": "stale",
                "agent": "pid:1",
                "operation": "update",
                "requested_at": time.time() - 120,
            }
        ),
        encoding="utf-8",
    )

    status = get_lock_queue_status(session_dir, max_age=1)
    assert status.pending == []
    assert not stale.exists()


def test_get_lock_queue_status_reports_position(tmp_path):
    session_dir = tmp_path
    queue_dir = session_dir / LOCK_QUEUE_DIR
    queue_dir.mkdir()
    first = queue_dir / "first.json"
    second = queue_dir / "second.json"
    first.write_text(
        json.dumps(
            {
                "id": "first",
                "agent": "agent-one",
                "operation": "status",
                "requested_at": time.time() - 2,
            }
        ),
        encoding="utf-8",
    )
    second.write_text(
        json.dumps(
            {
                "id": "second",
                "agent": "agent-two",
                "operation": "update",
                "requested_at": time.time() - 1,
            }
        ),
        encoding="utf-8",
    )

    status = get_lock_queue_status(session_dir, agent="agent-two")
    assert len(status.pending) == 2
    assert status.position == 2
