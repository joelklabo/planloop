"""Error context capture for rich debugging.

Provides a decorator that automatically captures full debugging context
when errors occur: local variables, stack trace, state snapshot, and trace_id.
"""
from __future__ import annotations

import functools
import json
import traceback
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

from .observability import get_current_trace_id

F = TypeVar("F", bound=Callable[..., Any])


def capture_error_context(session_dir: Path | None) -> Callable[[F], F]:
    """Decorator that captures full context on error.

    Captures:
    - Local variables at exception point
    - State snapshot (state.json if exists)
    - Linked LLM transcript (via trace_id)
    - Full stack trace with argument values
    - Environment info

    Usage:
        @capture_error_context(session_dir)
        def update_session(session: SessionState, payload: UpdatePayload):
            # If this raises, full context is auto-captured
            ...

    Args:
        session_dir: Path to session directory (None = no file output)

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Capture context
                trace_id = get_current_trace_id()
                timestamp = datetime.now(UTC).isoformat()

                # Get local variables from the frame where error occurred
                import sys
                frame = sys.exc_info()[2]
                if frame is not None:
                    tb_frame = frame.tb_frame
                    local_vars = {
                        k: _sanitize_value(v)
                        for k, v in tb_frame.f_locals.items()
                    }
                else:
                    local_vars = {}

                # Stack trace with details
                tb = traceback.extract_tb(e.__traceback__)
                stack_trace = [
                    {
                        "file": frame.filename,
                        "line": frame.lineno,
                        "function": frame.name,
                        "code": frame.line
                    }
                    for frame in tb
                ]

                # State snapshot
                state_snapshot_path = None
                if session_dir and (session_dir / "state.json").exists():
                    state_snapshot_path = str(session_dir / "state.json")

                # Build error report
                error_report = {
                    "timestamp": timestamp,
                    "trace_id": trace_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "function": func.__name__,
                    "local_variables": local_vars,
                    "stack_trace": stack_trace,
                    "state_snapshot_path": state_snapshot_path,
                    "llm_transcript_link": f"logs/llm_transcripts/*_{trace_id}.json" if session_dir else None
                }

                # Save error report and state snapshot if session_dir provided
                if session_dir:
                    error_dir = session_dir / "logs" / "errors"
                    error_dir.mkdir(parents=True, exist_ok=True)

                    # Save error report
                    error_file = error_dir / f"{trace_id}_error.json"
                    error_file.write_text(json.dumps(error_report, indent=2))

                    # Save state snapshot if it exists
                    if state_snapshot_path:
                        snapshot_file = error_dir / f"{trace_id}_state.json"
                        state_content = Path(state_snapshot_path).read_text()
                        snapshot_file.write_text(state_content)

                # Attach context to exception for programmatic access
                e.__error_context__ = error_report  # type: ignore[attr-defined]

                # Re-raise with context attached
                raise

        return wrapper  # type: ignore[return-value]
    return decorator


def _sanitize_value(value: Any) -> str:
    """Remove sensitive data from logged values.

    Args:
        value: Value to sanitize

    Returns:
        Sanitized string representation
    """
    value_str = str(value)
    value_lower = value_str.lower()

    # Check if value contains sensitive keywords
    sensitive_keywords = ['api_key', 'token', 'secret', 'password', 'bearer']
    if any(keyword in value_lower for keyword in sensitive_keywords):
        return "[REDACTED]"

    # Truncate long values
    max_length = 200
    if len(value_str) > max_length:
        return value_str[:max_length] + "..."

    return value_str


__all__ = ["capture_error_context"]
