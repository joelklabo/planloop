"""Tests for error context capture decorator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from planloop.dev_mode.error_context import capture_error_context
from planloop.dev_mode.observability import set_trace_id


class TestErrorContextCapture:
    """Test error context capture decorator."""

    def test_decorator_captures_error_context(self, tmp_path: Path):
        """Decorator should capture full context when error occurs."""
        session_dir = tmp_path / "session"
        session_dir.mkdir()

        set_trace_id("tr_test_error_001")

        @capture_error_context(session_dir)
        def failing_function(x: int, y: str) -> None:
            local_var = "test_value"  # noqa: F841
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function(42, "hello")

        # Check error report was created
        error_dir = session_dir / "logs" / "errors"
        assert error_dir.exists()

        error_files = list(error_dir.glob("tr_test_error_001_error.json"))
        assert len(error_files) == 1

        # Verify error report content
        error_data = json.loads(error_files[0].read_text())
        assert error_data["trace_id"] == "tr_test_error_001"
        assert error_data["error_type"] == "ValueError"
        assert error_data["error_message"] == "Test error"
        assert error_data["function"] == "failing_function"
        assert "local_variables" in error_data
        assert "stack_trace" in error_data

    def test_decorator_sanitizes_sensitive_data(self, tmp_path: Path):
        """Decorator should redact sensitive data from logs."""
        session_dir = tmp_path / "session"
        session_dir.mkdir()

        set_trace_id("tr_test_sanitize_001")

        @capture_error_context(session_dir)
        def function_with_secrets() -> None:
            api_key = "sk-secret123"  # noqa: F841
            token = "bearer_token_xyz"  # noqa: F841
            password = "mypassword"  # noqa: F841
            normal_var = "not_sensitive"  # noqa: F841
            raise RuntimeError("Oops")

        with pytest.raises(RuntimeError):
            function_with_secrets()

        error_dir = session_dir / "logs" / "errors"
        error_files = list(error_dir.glob("tr_test_sanitize_001_error.json"))
        error_data = json.loads(error_files[0].read_text())

        # Check that sensitive values are redacted
        local_vars_str = str(error_data.get("local_variables", {}))
        assert "REDACTED" in local_vars_str or "sk-secret123" not in local_vars_str

    def test_decorator_captures_state_snapshot(self, tmp_path: Path):
        """Decorator should save state snapshot when state.json exists."""
        session_dir = tmp_path / "session"
        session_dir.mkdir()

        # Create a fake state.json
        state_data = {"version": 5, "tasks": [{"id": 1, "status": "IN_PROGRESS"}]}
        (session_dir / "state.json").write_text(json.dumps(state_data))

        set_trace_id("tr_test_state_001")

        @capture_error_context(session_dir)
        def failing_with_state() -> None:
            raise KeyError("Missing key")

        with pytest.raises(KeyError):
            failing_with_state()

        # Check state snapshot was saved
        error_dir = session_dir / "logs" / "errors"
        state_files = list(error_dir.glob("tr_test_state_001_state.json"))
        assert len(state_files) == 1

        # Verify snapshot content
        snapshot_data = json.loads(state_files[0].read_text())
        assert snapshot_data["version"] == 5
        assert len(snapshot_data["tasks"]) == 1

    def test_decorator_without_session_dir(self):
        """Decorator should work without session_dir (no file output)."""
        set_trace_id("tr_test_no_dir_001")

        @capture_error_context(None)
        def failing_no_dir() -> None:
            raise TypeError("Type mismatch")

        # Should still raise error, just no files written
        with pytest.raises(TypeError, match="Type mismatch"):
            failing_no_dir()

    def test_decorator_attaches_context_to_exception(self, tmp_path: Path):
        """Decorator should attach error context to exception object."""
        session_dir = tmp_path / "session"
        session_dir.mkdir()

        set_trace_id("tr_test_attach_001")

        @capture_error_context(session_dir)
        def failing_attach() -> None:
            raise ZeroDivisionError("Division by zero")

        try:
            failing_attach()
        except ZeroDivisionError as e:
            # Check that context was attached
            assert hasattr(e, "__error_context__")
            context = e.__error_context__
            assert context["trace_id"] == "tr_test_attach_001"
            assert context["error_type"] == "ZeroDivisionError"

    def test_decorator_preserves_function_metadata(self, tmp_path: Path):
        """Decorator should preserve original function name and docstring."""
        session_dir = tmp_path / "session"
        session_dir.mkdir()

        @capture_error_context(session_dir)
        def documented_function(x: int) -> int:
            """This is a documented function."""
            return x * 2

        assert documented_function.__name__ == "documented_function"
        assert "documented function" in documented_function.__doc__

    def test_decorator_successful_execution(self, tmp_path: Path):
        """Decorator should not interfere with successful execution."""
        session_dir = tmp_path / "session"
        session_dir.mkdir()

        @capture_error_context(session_dir)
        def successful_function(x: int, y: int) -> int:
            return x + y

        result = successful_function(5, 3)
        assert result == 8

        # No error files should be created
        error_dir = session_dir / "logs" / "errors"
        if error_dir.exists():
            assert len(list(error_dir.glob("*.json"))) == 0
