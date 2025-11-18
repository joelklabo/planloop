"""Performance span tracing for operation breakdown.

Provides a context manager for tracking operation duration and metadata,
with output to trace files for analysis.
"""
from __future__ import annotations

import json
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

from .observability import get_current_trace_id


@contextmanager
def trace_span(
    name: str,
    session_dir: Path | None = None,
    **metadata: Any,
) -> Generator[None, None, None]:
    """Context manager to track performance span.
    
    Records the duration of an operation along with any metadata.
    Multiple spans for the same trace_id are appended to the same file.
    
    Usage:
        with trace_span("llm_call", session_dir=session_dir, model="gpt-4"):
            result = call_llm()
        
        with trace_span("parse_response", session_dir=session_dir):
            data = parse(result)
    
    Args:
        name: Operation name (e.g., "llm_call", "parse_response")
        session_dir: Path to session directory (None = no file output)
        **metadata: Additional metadata to attach to the span
    
    Yields:
        None
    """
    trace_id = get_current_trace_id()
    start_time = time.time()
    start_iso = datetime.now(timezone.utc).isoformat()
    
    try:
        yield
    finally:
        end_time = time.time()
        end_iso = datetime.now(timezone.utc).isoformat()
        duration_ms = (end_time - start_time) * 1000
        
        span_data = {
            "name": name,
            "start_time": start_iso,
            "end_time": end_iso,
            "duration_ms": duration_ms,
            "metadata": metadata,
        }
        
        if session_dir:
            _write_span_to_trace_file(session_dir, trace_id, span_data)


def _write_span_to_trace_file(
    session_dir: Path,
    trace_id: str,
    span_data: dict[str, Any],
) -> None:
    """Write span data to trace file, appending if file exists.
    
    Args:
        session_dir: Path to session directory
        trace_id: Trace ID for this operation
        span_data: Span data to write
    """
    trace_dir = session_dir / "logs" / "traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_file = trace_dir / f"{trace_id}.json"
    
    # Load existing trace data or create new
    if trace_file.exists():
        trace_data = json.loads(trace_file.read_text())
    else:
        trace_data = {
            "trace_id": trace_id,
            "spans": [],
        }
    
    # Append new span
    trace_data["spans"].append(span_data)
    
    # Write back to file
    trace_file.write_text(json.dumps(trace_data, indent=2))


__all__ = ["trace_span"]
