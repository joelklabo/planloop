"""Development mode and observability features for planloop.

This module provides instrumentation for debugging, performance analysis,
and audit trails:
- Distributed tracing with trace IDs
- Error context capture
- Lock operation logging
- Performance span tracking
"""

from .error_context import capture_error_context
from .observability import generate_trace_id, get_current_trace_id, set_trace_id, start_operation_trace

__all__ = [
    "capture_error_context",
    "generate_trace_id",
    "get_current_trace_id",
    "set_trace_id",
    "start_operation_trace",
]
