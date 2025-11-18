"""Tests for lock operation instrumentation."""
from __future__ import annotations

import json
import time
from pathlib import Path

from planloop.core.lock import acquire_lock
from planloop.dev_mode.observability import set_trace_id


class TestLockOperationLogging:
    """Test lock operation logging."""

    def test_lock_operations_are_logged(self, tmp_path: Path):
        """Lock acquire and release should be logged."""
        session_dir = tmp_path / "test_session"
        session_dir.mkdir()

        set_trace_id("tr_lock_test_001")

        # Acquire and release lock using context manager
        with acquire_lock(session_dir, "test_operation", timeout=5):
            time.sleep(0.01)  # Brief hold time

        # Check log file exists
        log_file = session_dir / "logs" / "planloop.jsonl"
        assert log_file.exists(), "Lock log file should be created"

        # Read and parse log entries
        log_entries = []
        with open(log_file) as f:
            for line in f:
                if line.strip():
                    log_entries.append(json.loads(line))

        # Find lock-related entries
        lock_events = [e for e in log_entries if e.get("event", "").startswith("lock_")]

        # Should have at least requested, acquired, released
        assert len(lock_events) >= 3, f"Expected >=3 lock events, got {len(lock_events)}"

        # Verify event types
        event_types = [e["event"] for e in lock_events]
        assert "lock_requested" in event_types
        assert "lock_acquired" in event_types
        assert "lock_released" in event_types

    def test_lock_logging_includes_trace_id(self, tmp_path: Path):
        """Lock log entries should include trace_id."""
        session_dir = tmp_path / "test_session"
        session_dir.mkdir()

        set_trace_id("tr_lock_trace_002")

        with acquire_lock(session_dir, "traced_operation", timeout=5):
            pass

        log_file = session_dir / "logs" / "planloop.jsonl"
        log_entries = []
        with open(log_file) as f:
            for line in f:
                if line.strip():
                    log_entries.append(json.loads(line))

        lock_events = [e for e in log_entries if e.get("event", "").startswith("lock_")]

        # All lock events should have trace_id
        for event in lock_events:
            assert "trace_id" in event
            assert event["trace_id"] == "tr_lock_trace_002"

    def test_lock_logging_includes_timing(self, tmp_path: Path):
        """Lock log should include wait_ms and hold_ms."""
        session_dir = tmp_path / "test_session"
        session_dir.mkdir()

        set_trace_id("tr_lock_timing_003")

        with acquire_lock(session_dir, "timed_operation", timeout=5):
            time.sleep(0.05)  # Hold for 50ms

        log_file = session_dir / "logs" / "planloop.jsonl"
        log_entries = []
        with open(log_file) as f:
            for line in f:
                if line.strip():
                    log_entries.append(json.loads(line))

        lock_events = [e for e in log_entries if e.get("event", "").startswith("lock_")]

        # Find acquired event - should have wait_ms
        acquired = [e for e in lock_events if e["event"] == "lock_acquired"]
        assert len(acquired) > 0
        assert "wait_ms" in acquired[0]
        assert isinstance(acquired[0]["wait_ms"], (int, float))

        # Find released event - should have hold_ms
        released = [e for e in lock_events if e["event"] == "lock_released"]
        assert len(released) > 0
        assert "hold_ms" in released[0]
        assert released[0]["hold_ms"] >= 50  # We held for 50ms

    def test_lock_logging_includes_operation_name(self, tmp_path: Path):
        """Lock log should include operation name."""
        session_dir = tmp_path / "test_session"
        session_dir.mkdir()

        set_trace_id("tr_lock_op_004")

        with acquire_lock(session_dir, "update_task_status", timeout=5):
            pass

        log_file = session_dir / "logs" / "planloop.jsonl"
        log_entries = []
        with open(log_file) as f:
            for line in f:
                if line.strip():
                    log_entries.append(json.loads(line))

        lock_events = [e for e in log_entries if e.get("event", "").startswith("lock_")]

        # All events should have operation name
        for event in lock_events:
            assert "operation" in event
            assert event["operation"] == "update_task_status"

    def test_lock_logging_includes_entry_id(self, tmp_path: Path):
        """Lock log should include queue entry_id."""
        session_dir = tmp_path / "test_session"
        session_dir.mkdir()

        set_trace_id("tr_lock_entry_005")

        with acquire_lock(session_dir, "test_operation", timeout=5):
            pass

        log_file = session_dir / "logs" / "planloop.jsonl"
        log_entries = []
        with open(log_file) as f:
            for line in f:
                if line.strip():
                    log_entries.append(json.loads(line))

        lock_events = [e for e in log_entries if e.get("event", "").startswith("lock_")]

        # Find entry_id from requested event
        requested = [e for e in lock_events if e["event"] == "lock_requested"]
        assert len(requested) > 0
        assert "lock_entry_id" in requested[0]
        entry_id = requested[0]["lock_entry_id"]

        # All events should have same entry_id
        for event in lock_events:
            assert event.get("lock_entry_id") == entry_id
