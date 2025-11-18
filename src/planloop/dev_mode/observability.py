"""Distributed tracing with trace IDs for linking operations.

Provides trace ID generation and context management using contextvars
for thread-local trace propagation. Every operation can have a unique
trace_id that links errors, logs, LLM calls, state diffs, and performance data.
"""
from __future__ import annotations

import contextvars
import secrets
from datetime import UTC, datetime

# Thread-local trace context
_trace_context: contextvars.ContextVar[str | None] = contextvars.ContextVar("trace_context", default=None)


def generate_trace_id() -> str:
    """Generate a new trace ID.

    Format: tr_{timestamp}_{random}
    Example: tr_20251118112700_a3f5c9

    Returns:
        Unique trace ID string
    """
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    random = secrets.token_hex(3)  # 6 hex characters
    return f"tr_{timestamp}_{random}"


def set_trace_id(trace_id: str) -> None:
    """Set the current trace ID in context.

    Args:
        trace_id: Trace ID to set
    """
    _trace_context.set(trace_id)


def get_current_trace_id() -> str:
    """Get the current trace ID, or generate one if none exists.

    Returns:
        Current trace ID from context, or newly generated ID
    """
    trace_id = _trace_context.get()
    if not trace_id:
        trace_id = generate_trace_id()
        set_trace_id(trace_id)
    return trace_id


def start_operation_trace(operation: str) -> str:
    """Start a new trace for an operation.

    Generates a new trace ID and sets it in the context.
    Use this at the start of CLI commands or major operations.

    Args:
        operation: Operation name (e.g., "update", "suggest", "status")

    Returns:
        The new trace ID
    """
    trace_id = generate_trace_id()
    set_trace_id(trace_id)
    return trace_id


__all__ = [
    "generate_trace_id",
    "set_trace_id",
    "get_current_trace_id",
    "start_operation_trace",
]
