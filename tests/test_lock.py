"""Tests for session lock helpers."""
from __future__ import annotations

import threading
import time

import pytest

from planloop.core.lock import LOCK_FILE, acquire_lock, get_lock_status


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
