"""Tests for distributed tracing system (trace IDs)."""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

from planloop.dev_mode.observability import (
    generate_trace_id,
    get_current_trace_id,
    set_trace_id,
    start_operation_trace,
)


class TestTraceIDGeneration:
    """Test trace ID generation."""

    def test_generate_trace_id_format(self):
        """Trace IDs should have format tr_{timestamp}_{random}."""
        trace_id = generate_trace_id()

        # Format: tr_YYYYMMDDHHMMSS_XXXXXX (6 hex chars)
        pattern = r"^tr_\d{14}_[0-9a-f]{6}$"
        assert re.match(pattern, trace_id), f"Invalid format: {trace_id}"

    def test_generate_trace_id_uniqueness(self):
        """Multiple calls should generate unique IDs."""
        ids = [generate_trace_id() for _ in range(100)]
        assert len(set(ids)) == 100, "Trace IDs should be unique"

    def test_trace_id_starts_with_prefix(self):
        """All trace IDs should start with 'tr_'."""
        trace_id = generate_trace_id()
        assert trace_id.startswith("tr_")


class TestTraceIDContext:
    """Test trace ID context management."""

    def test_set_and_get_trace_id(self):
        """Should be able to set and retrieve trace ID."""
        test_id = "tr_20251118112700_abc123"
        set_trace_id(test_id)
        assert get_current_trace_id() == test_id

    def test_get_trace_id_generates_if_none(self):
        """get_current_trace_id should generate ID if none exists."""
        # Note: This test assumes fresh context
        trace_id = get_current_trace_id()
        assert trace_id is not None
        assert trace_id.startswith("tr_")

    def test_trace_id_persists_in_context(self):
        """Trace ID should persist across multiple get calls."""
        first_id = get_current_trace_id()
        second_id = get_current_trace_id()
        assert first_id == second_id

    def test_trace_id_isolation_between_threads(self):
        """Trace IDs should be isolated between threads."""
        results = []

        def get_id_in_thread():
            # Each thread starts fresh, should generate its own ID
            # However, thread pool may reuse threads, so we explicitly reset
            from planloop.dev_mode.observability import _trace_context
            _trace_context.set(None)
            return get_current_trace_id()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(get_id_in_thread) for _ in range(3)]
            results = [f.result() for f in futures]

        # All IDs should be unique (each thread generates independently)
        assert len(set(results)) == 3, f"Expected 3 unique IDs, got {len(set(results))}: {results}"


class TestStartOperationTrace:
    """Test operation trace initialization."""

    def test_start_operation_trace_returns_id(self):
        """start_operation_trace should return a trace ID."""
        trace_id = start_operation_trace("test_operation")
        assert trace_id is not None
        assert trace_id.startswith("tr_")

    def test_start_operation_trace_sets_context(self):
        """start_operation_trace should set trace ID in context."""
        trace_id = start_operation_trace("update")
        current_id = get_current_trace_id()
        assert current_id == trace_id

    def test_start_operation_creates_new_id(self):
        """Each start_operation_trace call creates a new ID."""
        id1 = start_operation_trace("operation1")
        id2 = start_operation_trace("operation2")
        assert id1 != id2
