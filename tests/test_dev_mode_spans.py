"""Tests for performance span tracing."""
from __future__ import annotations

import json
import time
from pathlib import Path

from planloop.dev_mode.observability import set_trace_id
from planloop.dev_mode.spans import trace_span


class TestTraceSpan:
    """Test the trace_span context manager."""

    def test_trace_span_records_duration(self, tmp_path: Path) -> None:
        """Test that trace_span records operation duration."""
        trace_id = "tr_test_123"
        set_trace_id(trace_id)

        with trace_span("test_operation", session_dir=tmp_path):
            time.sleep(0.01)  # Simulate work

        trace_file = tmp_path / "logs" / "traces" / f"{trace_id}.json"
        assert trace_file.exists()

        trace_data = json.loads(trace_file.read_text())
        assert trace_data["trace_id"] == trace_id
        assert "spans" in trace_data
        assert len(trace_data["spans"]) == 1

        span = trace_data["spans"][0]
        assert span["name"] == "test_operation"
        assert span["duration_ms"] >= 10  # At least 10ms from sleep
        assert "start_time" in span
        assert "end_time" in span

    def test_trace_span_with_metadata(self, tmp_path: Path) -> None:
        """Test that trace_span captures metadata."""
        trace_id = "tr_test_456"
        set_trace_id(trace_id)

        with trace_span("llm_call", session_dir=tmp_path, model="gpt-4", tokens=150):
            pass

        trace_file = tmp_path / "logs" / "traces" / f"{trace_id}.json"
        trace_data = json.loads(trace_file.read_text())

        span = trace_data["spans"][0]
        assert span["metadata"]["model"] == "gpt-4"
        assert span["metadata"]["tokens"] == 150

    def test_trace_span_appends_multiple_spans(self, tmp_path: Path) -> None:
        """Test that multiple spans are recorded to the same trace file."""
        trace_id = "tr_test_789"
        set_trace_id(trace_id)

        with trace_span("operation_1", session_dir=tmp_path):
            pass

        with trace_span("operation_2", session_dir=tmp_path):
            pass

        trace_file = tmp_path / "logs" / "traces" / f"{trace_id}.json"
        trace_data = json.loads(trace_file.read_text())

        assert len(trace_data["spans"]) == 2
        assert trace_data["spans"][0]["name"] == "operation_1"
        assert trace_data["spans"][1]["name"] == "operation_2"

    def test_trace_span_without_session_dir(self) -> None:
        """Test that trace_span works without session_dir (no file output)."""
        trace_id = "tr_test_999"
        set_trace_id(trace_id)

        # Should not raise, just skip file output
        with trace_span("no_output"):
            pass

    def test_trace_span_nested(self, tmp_path: Path) -> None:
        """Test nested trace spans."""
        trace_id = "tr_test_nested"
        set_trace_id(trace_id)

        with trace_span("outer", session_dir=tmp_path):
            time.sleep(0.01)
            with trace_span("inner", session_dir=tmp_path):
                time.sleep(0.01)

        trace_file = tmp_path / "logs" / "traces" / f"{trace_id}.json"
        trace_data = json.loads(trace_file.read_text())

        assert len(trace_data["spans"]) == 2
        # Spans are recorded in completion order (inner completes first)
        inner_span = trace_data["spans"][0]
        outer_span = trace_data["spans"][1]

        assert inner_span["name"] == "inner"
        assert outer_span["name"] == "outer"
        # Outer should take longer than inner
        assert outer_span["duration_ms"] >= inner_span["duration_ms"]
