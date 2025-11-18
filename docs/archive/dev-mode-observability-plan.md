# Planloop Development Mode & Observability Plan

**Version:** 2.1  
**Date:** 2025-11-18  
**Purpose:** Maximum observability for self-development with web-based visualization

---

## 🚀 Quick Start

### The 4 Critical Features (Implement First - Phase 1A)

These solve 80% of debugging problems with low-medium effort:

1. **⭐⭐⭐⭐⭐ Error Context Capture** - Captures local variables, state snapshot, stack trace on every error
2. **⭐⭐⭐⭐⭐ Lock Operation Logging** - Logs every lock request/acquire/release for concurrency debugging
3. **⭐⭐⭐⭐ Performance Spans** - Breaks down operation time (LLM, I/O, parsing)
4. **⭐⭐⭐⭐ Trace ID Linking** - Automatically links errors → LLM transcripts → state diffs

**Why these 4?** Based on analysis of 10 common software issues (race conditions, crashes, performance degradation, etc.), these 4 features solve 8 out of 10 scenarios.

See [Phase 1A](#phase-1a-critical-observability-features-week-1---high-priority) for detailed implementation.

---

## 🎯 Core Philosophy

**Data-first, visualization-second.** Capture everything useful about application state. CLI outputs structured data (JSON/JSONL). Web UI provides clean visualization. No fancy terminal UIs - keep CLI simple and scriptable.

### Priorities
1. **Capture comprehensive data** - Logs, traces, LLM calls, diffs, metrics
2. **Structured output** - JSON/JSONL for machine readability
3. **Web dashboard** - Clean, simple table-based UI for browsing
4. **Hot reload dev mode** - Editable install for fast iteration

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Browser (localhost:3000)                   │
│              Simple Next.js Dashboard                        │
│           • Sessions table (sortable, filterable)            │
│           • Session detail (tasks, logs, LLM calls)          │
│           • No fancy charts/graphs initially                 │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI (localhost:8000)                       │
│             REST API for reading data                        │
│          GET /api/sessions, /api/sessions/:id/logs          │
└────────────────────────┬─────────────────────────────────────┘
                         │ File I/O
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  ~/.planloop/ (Data Layer)                   │
│  sessions/<id>/                                             │
│    ├── state.json                  # Session state          │
│    ├── PLAN.md                     # Plan markdown          │
│    └── logs/                       # 🆕 Rich logging        │
│        ├── planloop.jsonl          # Structured events      │
│        ├── llm_transcripts/        # API request/response   │
│        │   └── 001_suggest.json                            │
│        ├── traces/                 # Command execution      │
│        │   └── 001_update.json                             │
│        ├── diffs/                  # State changes          │
│        │   ├── 001_pre.json                                │
│        │   └── 001_post.json                               │
│        └── performance.jsonl       # Timing data            │
└─────────────────────────────────────────────────────────────┘
```

**Key Principles:**
- **CLI is simple** - Outputs JSON to stdout or files
- **Data is rich** - Capture everything needed for debugging
- **Web is clean** - Table-based UI, no over-engineering
- **Foundation is solid** - Can add fancy visualizations later

---

## 📋 Implementation Phases

### Phase 1A: Critical Observability Features (Week 1 - HIGH PRIORITY)

**Goal:** Implement the 4 features that solve 80% of debugging problems

#### 1. ⭐⭐⭐⭐⭐ Error Context Capture (CRITICAL)

**Problem Solved:** When errors occur, developers lack context about what caused them. Stack traces show "where" but not "why" (what were the variable values? what was the state?).

**Implementation:** `src/planloop/dev_mode/error_context.py`

```python
"""Error context capture for rich debugging."""
import functools
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from ..home import SESSIONS_DIR, initialize_home
from .observability import get_current_trace_id


def capture_error_context(session_dir: Path | None = None):
    """Decorator that captures full context on error.
    
    Captures:
    - Local variables at exception point
    - State snapshot (state.json)
    - Linked LLM transcript (via trace_id)
    - Full stack trace with argument values
    - Environment info
    
    Usage:
        @capture_error_context(session_dir)
        def update_session(session: SessionState, payload: UpdatePayload):
            # If this raises, full context is captured
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Capture context
                trace_id = get_current_trace_id()
                timestamp = datetime.utcnow().isoformat()
                
                # Local variables (sanitize secrets)
                local_vars = {
                    k: _sanitize_value(v) 
                    for k, v in func.__code__.co_varnames
                }
                
                # Stack trace with values
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
                state_snapshot = None
                if session_dir and (session_dir / "state.json").exists():
                    state_snapshot = (session_dir / "state.json").read_text()
                
                # Build error report
                error_report = {
                    "timestamp": timestamp,
                    "trace_id": trace_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "function": func.__name__,
                    "local_variables": local_vars,
                    "stack_trace": stack_trace,
                    "state_snapshot_path": str(session_dir / "state.json") if state_snapshot else None,
                    "llm_transcript_link": f"logs/llm_transcripts/*_{trace_id}.json"
                }
                
                # Save error report
                if session_dir:
                    error_dir = session_dir / "logs" / "errors"
                    error_dir.mkdir(parents=True, exist_ok=True)
                    error_file = error_dir / f"{trace_id}_error.json"
                    error_file.write_text(json.dumps(error_report, indent=2))
                    
                    # Also save state snapshot
                    if state_snapshot:
                        snapshot_file = error_dir / f"{trace_id}_state.json"
                        snapshot_file.write_text(state_snapshot)
                
                # Re-raise with context attached
                e.__error_context__ = error_report
                raise
        
        return wrapper
    return decorator


def _sanitize_value(value: Any) -> Any:
    """Remove sensitive data from logged values."""
    if isinstance(value, str):
        # Redact API keys, tokens
        if any(key in value.lower() for key in ['api_key', 'token', 'secret', 'password']):
            return "[REDACTED]"
    return repr(value)[:200]  # Truncate long values
```

**Usage in existing code:**

```python
# In src/planloop/core/update.py
from ..dev_mode.error_context import capture_error_context

@capture_error_context(session_dir)
def apply_update(session_dir: Path, payload: UpdatePayload) -> SessionState:
    # Existing code
    # If any error occurs, full context is auto-captured
    ...
```

**Output:** When error occurs, creates:
- `logs/errors/{trace_id}_error.json` - Full error report
- `logs/errors/{trace_id}_state.json` - State snapshot at error time

**CLI to view:**
```bash
planloop dev errors list --session <id>
planloop dev errors show <trace_id>
```

---

#### 2. ⭐⭐⭐⭐⭐ Lock Operation Logging (CRITICAL)

**Problem Solved:** Concurrency bugs (race conditions, deadlocks) are invisible without lock visibility. Developers can't see who's waiting for whom.

**Implementation:** `src/planloop/core/lock.py` (enhancement)

```python
"""Add detailed logging to lock operations."""
from ..dev_mode.observability import log_lock_event, get_current_trace_id

# In _register_queue_entry()
def _register_queue_entry(session_dir: Path, entry: QueueEntry) -> None:
    # ... existing code ...
    
    # ADD: Log lock requested
    log_lock_event(
        session_dir=session_dir,
        event="lock_requested",
        trace_id=get_current_trace_id(),
        operation=entry.operation,
        entry_id=entry.id,
        timestamp=datetime.utcnow()
    )

# In acquire_lock()
def acquire_lock(session_dir: Path, operation: str, timeout: float = 60.0) -> LockHandle:
    request_time = datetime.utcnow()
    # ... existing wait logic ...
    
    acquired_time = datetime.utcnow()
    wait_ms = (acquired_time - request_time).total_seconds() * 1000
    
    # ADD: Log lock acquired
    log_lock_event(
        session_dir=session_dir,
        event="lock_acquired",
        trace_id=get_current_trace_id(),
        operation=operation,
        entry_id=entry.id,
        wait_ms=wait_ms,
        timestamp=acquired_time
    )
    
    # ... return handle ...

# In release_lock()
def release_lock(handle: LockHandle) -> None:
    release_time = datetime.utcnow()
    hold_ms = (release_time - handle.acquired_at).total_seconds() * 1000
    
    # ADD: Log lock released
    log_lock_event(
        session_dir=handle.session_dir,
        event="lock_released",
        trace_id=get_current_trace_id(),
        operation=handle.operation,
        entry_id=handle.entry_id,
        hold_ms=hold_ms,
        timestamp=release_time
    )
    
    # ... existing release logic ...
```

**Supporting function in observability.py:**

```python
def log_lock_event(
    session_dir: Path,
    event: str,
    trace_id: str,
    operation: str,
    entry_id: str,
    timestamp: datetime,
    wait_ms: float | None = None,
    hold_ms: float | None = None
) -> None:
    """Log a lock-related event."""
    log_entry = {
        "timestamp": timestamp.isoformat(),
        "event": event,
        "trace_id": trace_id,
        "operation": operation,
        "lock_entry_id": entry_id,
        "wait_ms": wait_ms,
        "hold_ms": hold_ms
    }
    
    # Write to planloop.jsonl
    log_file = session_dir / "logs" / "planloop.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

**Output:** Log entries like:
```json
{"timestamp":"...","event":"lock_requested","trace_id":"tr_abc","operation":"update","lock_entry_id":"entry_123"}
{"timestamp":"...","event":"lock_acquired","trace_id":"tr_abc","operation":"update","wait_ms":234}
{"timestamp":"...","event":"lock_released","trace_id":"tr_abc","operation":"update","hold_ms":2345}
```

**CLI to view:**
```bash
planloop dev locks --session <id>  # Show all lock operations
planloop dev locks --session <id> --waiting  # Show current waiters
```

---

#### 3. ⭐⭐⭐⭐ Performance Spans (HIGH VALUE)

**Problem Solved:** Developers see "operation took 5 seconds" but don't know if it's LLM, file I/O, or parsing. Need breakdown.

**Implementation:** `src/planloop/dev_mode/spans.py`

```python
"""Span-based performance tracing."""
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Generator

from .observability import get_current_trace_id


@dataclass
class Span:
    """A timed operation span."""
    name: str
    start_time: float
    end_time: float | None = None
    duration_ms: float | None = None
    parent: str | None = None
    metadata: dict = field(default_factory=dict)


_active_spans: dict[str, list[Span]] = {}


@contextmanager
def trace_span(name: str, **metadata) -> Generator[None, None, None]:
    """Context manager for tracing a span.
    
    Usage:
        with trace_span("llm_call", provider="anthropic", model="claude"):
            result = llm.generate(...)
    """
    trace_id = get_current_trace_id()
    
    span = Span(
        name=name,
        start_time=time.time(),
        metadata=metadata
    )
    
    # Track active spans for this trace
    if trace_id not in _active_spans:
        _active_spans[trace_id] = []
    _active_spans[trace_id].append(span)
    
    try:
        yield
    finally:
        span.end_time = time.time()
        span.duration_ms = (span.end_time - span.start_time) * 1000


def get_trace_spans(trace_id: str) -> list[Span]:
    """Get all spans for a trace."""
    return _active_spans.get(trace_id, [])


def write_trace_spans(session_dir: Path, trace_id: str) -> None:
    """Write collected spans to trace file."""
    spans = get_trace_spans(trace_id)
    if not spans:
        return
    
    trace_data = {
        "trace_id": trace_id,
        "timestamp": datetime.utcnow().isoformat(),
        "spans": [
            {
                "name": s.name,
                "duration_ms": s.duration_ms,
                "metadata": s.metadata
            }
            for s in spans
        ],
        "total_duration_ms": sum(s.duration_ms for s in spans if s.duration_ms)
    }
    
    traces_dir = session_dir / "logs" / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)
    
    trace_file = traces_dir / f"{trace_id}.json"
    trace_file.write_text(json.dumps(trace_data, indent=2))
    
    # Clean up
    _active_spans.pop(trace_id, None)
```

**Usage in code:**

```python
# In src/planloop/core/update.py
from ..dev_mode.spans import trace_span, write_trace_spans

def apply_update(session_dir: Path, payload: UpdatePayload) -> SessionState:
    trace_id = get_current_trace_id()
    
    with trace_span("load_state"):
        state = load_session_state_from_disk(session_dir)
    
    with trace_span("llm_suggest", provider=config.provider, model=config.model):
        suggestion = llm_client.generate(prompt)
    
    with trace_span("parse_response"):
        parsed = parse_suggestion(suggestion)
    
    with trace_span("save_state"):
        save_session_state(session_dir, new_state)
    
    # Write spans at end
    write_trace_spans(session_dir, trace_id)
    
    return new_state
```

**Output:** `logs/traces/{trace_id}.json`:
```json
{
  "trace_id": "tr_abc123",
  "timestamp": "2025-11-18T08:30:00Z",
  "spans": [
    {"name": "load_state", "duration_ms": 12},
    {"name": "llm_suggest", "duration_ms": 2300, "metadata": {"provider": "anthropic"}},
    {"name": "parse_response", "duration_ms": 5},
    {"name": "save_state", "duration_ms": 34}
  ],
  "total_duration_ms": 2351
}
```

**CLI to view:**
```bash
planloop dev perf --session <id>  # List all traces with durations
planloop dev perf show <trace_id>  # Show span breakdown
```

---

#### 4. ⭐⭐⭐⭐ Trace ID Linking (HIGH VALUE)

**Problem Solved:** Hard to connect related events (error → LLM call → state diff). Need automatic linking.

**Implementation:** `src/planloop/dev_mode/observability.py`

```python
"""Trace ID management and linking."""
import contextvars
import secrets
from datetime import datetime
from pathlib import Path


# Thread-local trace context
_trace_context = contextvars.ContextVar("trace_context", default=None)


def generate_trace_id() -> str:
    """Generate a new trace ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random = secrets.token_hex(3)
    return f"tr_{timestamp}_{random}"


def set_trace_id(trace_id: str) -> None:
    """Set the current trace ID."""
    _trace_context.set(trace_id)


def get_current_trace_id() -> str:
    """Get the current trace ID, or generate one if none exists."""
    trace_id = _trace_context.get()
    if not trace_id:
        trace_id = generate_trace_id()
        set_trace_id(trace_id)
    return trace_id


def start_operation_trace(operation: str) -> str:
    """Start a new trace for an operation."""
    trace_id = generate_trace_id()
    set_trace_id(trace_id)
    return trace_id
```

**Usage in CLI:**

```python
# In src/planloop/cli.py
from .dev_mode.observability import start_operation_trace

@app.command()
def update(session: str):
    """Update a session."""
    trace_id = start_operation_trace("update")
    
    # All subsequent code uses this trace_id automatically
    # - Logs include it
    # - LLM transcripts include it
    # - State diffs include it
    # - Error reports include it
    
    try:
        result = do_update(session)
    except Exception as e:
        # Error report will have trace_id
        # Can link to LLM transcript via trace_id
        raise
```

**Automatic linking in recorder:**

```python
# In src/planloop/dev_mode/recorder.py
def record_llm_call(request, response, duration_ms):
    trace_id = get_current_trace_id()  # Automatic!
    
    transcript = {
        "trace_id": trace_id,  # Links to everything else
        "timestamp": datetime.utcnow().isoformat(),
        "request": request,
        "response": response,
        "duration_ms": duration_ms
    }
    
    # Filename includes trace_id for easy lookup
    filename = f"logs/llm_transcripts/{trace_id}_llm.json"
    ...
```

**Benefit:** Now when you see an error with `trace_id: tr_20251118_abc123`, you can instantly find:
- Error report: `logs/errors/tr_20251118_abc123_error.json`
- LLM transcript: `logs/llm_transcripts/tr_20251118_abc123_llm.json`
- Performance trace: `logs/traces/tr_20251118_abc123.json`
- State diff: Check `logs/diffs/*.json` for matching trace_id

**CLI helper:**
```bash
planloop dev trace <trace_id> --session <id>
# Shows: error (if any), LLM call, performance spans, state diff
# All in one view
```

---

### Phase 1B: Foundation Features (Week 1)

**Goal:** Basic dev mode + data capture infrastructure

**Deliverables:**

1. **Dev Mode Management** (`src/planloop/dev_mode/manager.py`)
   ```bash
   planloop dev on       # Enable hot-reload mode
   planloop dev off      # Switch back to stable
   planloop dev status   # Show mode (outputs JSON)
   planloop dev dogfood  # Full setup for self-dev
   ```

2. **Structured Logging** (`src/planloop/dev_mode/observability.py`)
   - Replace `.log` with `.jsonl` format
   - Every log entry includes: timestamp, level, trace_id, operation, message, context
   - Example:
     ```json
     {"timestamp":"2025-11-18T08:00:00Z","level":"INFO","trace_id":"tr_abc","operation":"update","message":"Starting update","session_id":"honk-xyz"}
     ```

3. **LLM Transcript Recording** (`src/planloop/dev_mode/recorder.py`)
   - Save every LLM API call to `logs/llm_transcripts/<trace_id>_llm.json`
   - Include: prompt, response, tokens, duration, cost
   - Environment variable to enable: `PLANLOOP_RECORD_LLM=1`

4. **State Diff Tracking**
   - Before/after snapshots: `logs/diffs/<trace_id>_pre.json` and `_post.json`
   - Computed diff saved in metadata

5. **Basic Performance Metrics**
   - JSONL stream: `logs/performance.jsonl`
   - Metrics: command duration, memory usage

**CLI Commands:**
```bash
# Dev mode
planloop dev on
planloop dev status --json

# Export data (all output JSON to stdout)
planloop dev export-logs --session <id>
planloop dev export-llm --session <id>
planloop dev export-traces --session <id>
planloop dev export-diffs --session <id>
```

---

### Phase 2: FastAPI Endpoints (Week 2)

**Goal:** REST API for reading captured data

**Endpoints:**
```
GET  /api/dev/status                      # Dev mode status
GET  /api/sessions                        # List sessions
GET  /api/sessions/:id                    # Session detail
GET  /api/sessions/:id/logs               # JSONL logs
GET  /api/sessions/:id/llm-calls          # LLM transcripts
GET  /api/sessions/:id/traces             # Command traces
GET  /api/sessions/:id/diffs              # State diffs
GET  /api/sessions/:id/performance        # Metrics
```

**Implementation:**
- Extend existing `src/planloop/web/server.py`
- Add routes in `src/planloop/web/routes/`
- Simple file reading, no complex processing
- CORS enabled for localhost:3000

---

### Phase 3: Web Dashboard MVP (Week 2-3)

**Goal:** Clean, simple UI for browsing data

**Tech Stack:**
- Next.js 14.2 (App Router)
- Tailwind CSS
- shadcn/ui components
- No charts initially (just tables)

**Pages:**

1. **Home: Sessions Table** (`/`)
   - Columns: Name, Title, Status, Updated, Tasks Progress
   - Sortable, filterable
   - Click → Session detail

2. **Session Detail** (`/sessions/:id`)
   - Tabs: Tasks | Plan | Logs | LLM Calls | Performance
   - **Tasks:** Table of tasks with status badges
   - **Plan:** Rendered PLAN.md
   - **Logs:** Table of log entries (searchable)
   - **LLM Calls:** Table of API calls (expandable rows)
   - **Performance:** Simple table of metrics

**Design:**
- Clean, minimal
- Tables with search/filter
- No fancy charts (can add later)
- Fast loading (<500ms)

---

### Phase 4: Additional Observability Features (Future - LOW PRIORITY)

**Goal:** Add features from debugging scenario analysis

These features solve remaining edge cases and improve UX. Implement only after Phase 1-3 are solid.

#### Tier 2: High Value Features

**5. ⭐⭐⭐⭐ Comparison Tool for Runs**
- **Solves:** Intermittent test failures
- **What:** Compare two traces side-by-side (diff logs, LLM responses, performance)
- **CLI:** `planloop dev compare <trace_id_1> <trace_id_2>`
- **Effort:** Medium

**6. ⭐⭐⭐⭐ Data Validation Logging**
- **Solves:** Silent data corruption
- **What:** Log Pydantic validation failures, schema mismatches, constraint violations
- **Implementation:** Wrap Pydantic model validation
- **Effort:** Medium

**7. ⭐⭐⭐⭐ Rate Limiting Metrics & Recommendations**
- **Solves:** API rate limiting issues
- **What:** Track LLM requests per minute, detect rate limits, suggest retry delays
- **CLI:** `planloop dev rate-limits --session <id>`
- **Effort:** Low

#### Tier 3: Nice to Have

**8. ⭐⭐⭐ Memory Profiling Snapshots**
- **Solves:** Memory leaks
- **What:** Take memory snapshots at intervals, log object counts by type
- **Implementation:** Use `tracemalloc`
- **Effort:** High

**9. ⭐⭐⭐ File Consistency Checks**
- **Solves:** State desynchronization
- **What:** Verify PLAN.md matches state.json, check file hashes
- **Effort:** Low

**10. ⭐⭐⭐ Deadlock Detection**
- **Solves:** Lock queue deadlocks
- **What:** Detect circular wait conditions, alert on deadlock
- **Effort:** High

#### Tier 4: Advanced (Long-term)

**11. ⭐⭐ Real-time Log Streaming (SSE)**
- Web UI feature for live log tailing
- Effort: Medium

**12. ⭐⭐ Diff Viewer (Web UI)**
- Side-by-side JSON diff with syntax highlighting
- Effort: Medium

**13. ⭐⭐ Trace Visualization**
- Waterfall charts, flame graphs
- Effort: High

**14. ⭐⭐ Correlation Analysis**
- "Duration correlates with state.json size"
- Effort: High

**15. ⭐ Root Cause Analysis (ML)**
- Automatic RCA for cascading failures
- Effort: Very High

---

## 🔧 Dev Mode Technical Details

### Hot Reload Setup

**How it works:**
1. Uninstall pipx version: `pipx uninstall planloop`
2. Install editable: `pip install -e ~/code/planloop`
3. Symlink binary: `~/.local/bin/planloop` → `.venv/bin/planloop`
4. State file: `~/.planloop/.dev_mode` (contains "dev")

**Safety:**
- Backup stable binary before switching
- Git tag: `dev-start-<timestamp>`
- Rollback command: `planloop dev restore`

### State Files

**~/.planloop/.dev_mode.json:**
```json
{
  "mode": "dev",
  "enabled_at": "2025-11-18T08:00:00Z",
  "repo_path": "/Users/honk/code/planloop",
  "git_commit": "abc123",
  "backup_path": "~/.local/bin/planloop.stable",
  "features": {
    "llm_recording": true,
    "tracing": true,
    "profiling": true
  }
}
```

---

## 📝 Logging Formats

### Standard Log Entry (JSONL)
```json
{
  "timestamp": "2025-11-18T08:14:17.585Z",
  "level": "INFO",
  "trace_id": "tr_abc123",
  "session_id": "honk-xyz",
  "operation": "update",
  "message": "Starting update operation",
  "context": {
    "task_id": 5,
    "user": "honk"
  },
  "duration_ms": null
}
```

### LLM Transcript
```json
{
  "trace_id": "tr_abc123",
  "timestamp": "2025-11-18T08:14:18.000Z",
  "operation": "suggest",
  "provider": "anthropic",
  "model": "claude-3-5-sonnet-20241022",
  "request": {
    "system": "You are an AI assistant...",
    "prompt": "Given the current state...",
    "max_tokens": 4000,
    "temperature": 0.7
  },
  "response": {
    "content": "Here's my suggestion...",
    "stop_reason": "end_turn",
    "usage": {
      "input_tokens": 1234,
      "output_tokens": 567
    }
  },
  "duration_ms": 2345,
  "cost_usd": 0.0234,
  "error": null
}
```

### Command Trace
```json
{
  "trace_id": "tr_abc123",
  "command": ["planloop", "update", "--session", "honk-xyz"],
  "started_at": "2025-11-18T08:14:17.585Z",
  "completed_at": "2025-11-18T08:14:20.123Z",
  "duration_ms": 2538,
  "status": "success",
  "spans": [
    {"name": "load_session", "duration_ms": 45},
    {"name": "llm_suggest", "duration_ms": 2300},
    {"name": "save_session", "duration_ms": 73}
  ]
}
```

### State Diff
```json
{
  "trace_id": "tr_abc123",
  "operation": "update",
  "timestamp": "2025-11-18T08:14:20.123Z",
  "before_file": "logs/diffs/001_pre.json",
  "after_file": "logs/diffs/001_post.json",
  "changes": {
    "tasks[4].status": {"old": "TODO", "new": "DONE"},
    "version": {"old": 11, "new": 12}
  }
}
```

### Performance Metric
```json
{"timestamp":"2025-11-18T08:14:20Z","metric":"command.duration","value":2538,"tags":{"command":"update"}}
{"timestamp":"2025-11-18T08:14:18Z","metric":"llm.latency","value":2300,"tags":{"provider":"anthropic"}}
{"timestamp":"2025-11-18T08:14:20Z","metric":"memory.rss_mb","value":45.2,"tags":{}}
```

---

## 🎓 Usage Examples

### Example 1: Enable Dev Mode
```bash
cd ~/code/planloop
planloop dev dogfood

# Output:
# ✅ Dev mode enabled
# 📁 Repo: /Users/honk/code/planloop
# 🔗 Symlink: ~/.local/bin/planloop → .venv/bin/planloop
# 🏷️  Tagged: dev-start-20251118-0800
# 📊 Features: LLM recording ✓ | Tracing ✓ | Profiling ✓
# 🌐 Start web: planloop web --port 8000
# 🎨 Frontend: cd frontend && npm run dev
```

### Example 2: Check What's Being Logged
```bash
# View recent logs
planloop dev export-logs --session honk-xyz --tail 50 | jq

# View LLM calls
planloop dev export-llm --session honk-xyz | jq

# Check performance
planloop dev export-performance --session honk-xyz | jq '.[] | select(.metric=="llm.latency")'
```

### Example 3: Debug a Failed Operation
```bash
# Run operation
planloop update --session honk-xyz
# (fails with error)

# Check logs around the error
planloop dev export-logs --session honk-xyz --tail 100 | jq 'select(.level=="ERROR")'

# Find the trace ID
TRACE_ID=$(planloop dev export-logs --session honk-xyz --tail 1 | jq -r '.trace_id')

# Get full trace
planloop dev export-traces --session honk-xyz | jq ".[] | select(.trace_id==\"$TRACE_ID\")"

# Check LLM transcript for that trace
planloop dev export-llm --session honk-xyz | jq ".[] | select(.trace_id==\"$TRACE_ID\")"

# View state diff
planloop dev export-diffs --session honk-xyz | jq ".[] | select(.trace_id==\"$TRACE_ID\")"
```

### Example 4: Web Dashboard
```bash
# Terminal 1: Start backend
planloop web --port 8000

# Terminal 2: Start frontend
cd frontend && npm run dev

# Browser
open http://localhost:3000

# Navigate:
# - Home: See all sessions in table
# - Click session: See tasks, logs, LLM calls
# - Search logs: Type "error" to filter
# - View LLM call: Click row to expand request/response
```

---

## 📊 Success Criteria

**Phase 1 (Week 1):**
- ✅ Dev mode switches in < 30 seconds
- ✅ All logs are JSONL structured
- ✅ LLM calls recorded with 100% coverage
- ✅ State diffs captured for all updates
- ✅ Performance metrics logged

**Phase 2 (Week 2):**
- ✅ FastAPI serves all data via REST
- ✅ API responses < 200ms for logs
- ✅ CORS configured for localhost

**Phase 3 (Week 2-3):**
- ✅ Sessions table loads < 500ms
- ✅ All data viewable in web UI
- ✅ Tables searchable/filterable
- ✅ UI is clean and responsive

---

## 🔐 Privacy & Security

- All data stored locally in `~/.planloop/`
- No cloud uploads
- LLM transcripts may contain sensitive code
- Environment variable to disable: `PLANLOOP_NO_RECORDING=1`
- Scrubbing tool: `planloop dev scrub --session <id>`

---

## 📚 File Structure

```
planloop/
├── src/planloop/
│   ├── dev_mode/                  # 🆕 New module
│   │   ├── __init__.py
│   │   ├── manager.py            # Dev/stable switching
│   │   ├── observability.py      # Logging, tracing
│   │   └── recorder.py           # LLM, diffs, metrics
│   ├── web/
│   │   ├── server.py             # Enhanced FastAPI
│   │   └── routes/
│   │       ├── sessions.py
│   │       ├── logs.py
│   │       └── dev.py
│   └── cli.py                    # Add dev subcommand
│
├── frontend/                      # 🆕 Next.js app
│   ├── app/
│   │   ├── page.tsx              # Sessions table
│   │   └── sessions/
│   │       └── [id]/
│   │           └── page.tsx      # Session detail
│   ├── components/
│   │   ├── ui/                   # shadcn components
│   │   ├── sessions-table.tsx
│   │   └── log-viewer.tsx
│   └── package.json
│
└── ~/.planloop/
    ├── .dev_mode                  # State marker
    ├── .dev_mode.json             # Extended state
    └── sessions/<id>/
        └── logs/
            ├── planloop.jsonl      # Structured logs
            ├── llm_transcripts/    # API calls
            ├── traces/             # Command traces
            ├── diffs/              # State diffs
            └── performance.jsonl   # Metrics
```

---

## 🚀 Implementation Priority

### IMMEDIATE (Phase 1A - Week 1)

These 4 features solve 80% of debugging problems:

1. **⭐⭐⭐⭐⭐ Error Context Capture** - Full context on every error
2. **⭐⭐⭐⭐⭐ Lock Operation Logging** - Visibility into concurrency
3. **⭐⭐⭐⭐ Performance Spans** - Breakdown of operation timing
4. **⭐⭐⭐⭐ Trace ID Linking** - Connect related events automatically

### SHORT-TERM (Phase 1B-3 - Week 1-3)

Foundation features:
- Dev mode management (on/off/dogfood)
- Structured JSONL logging
- LLM transcript recording
- State diff tracking
- FastAPI endpoints
- Simple web dashboard

### LONG-TERM (Phase 4 - Future)

Lower priority features:
- Comparison tool for runs
- Data validation logging
- Rate limiting metrics
- Memory profiling
- Deadlock detection
- Advanced visualizations

---

## 📊 Success Metrics

**Phase 1A Complete When:**
- ✅ All errors capture local variables + state snapshot
- ✅ Every lock operation logged with timing
- ✅ All operations have performance span breakdown
- ✅ All trace_ids link errors → LLM → diffs

**Phase 1B-3 Complete When:**
- ✅ Dev mode switches in < 30 seconds
- ✅ All logs are JSONL with trace_ids
- ✅ LLM calls recorded 100%
- ✅ Web UI shows all captured data

---

## 🎯 Key Insights from Analysis

Based on 10 real debugging scenarios:

1. **Context beats quantity** - Rich context on one error > 1000 basic logs
2. **Correlation is king** - Linking events (error→LLM→diff) is huge
3. **Concurrency needs visibility** - Locks, queues are major pain points
4. **Performance needs breakdown** - Total time is useless without spans
5. **Validation should be loud** - Silent corruption is the worst
6. **Comparison is essential** - For intermittent bugs

The 4 critical features (Phase 1A) solve these directly.

---

**END OF PLAN**

This plan prioritizes **capturing maximum useful data** with **immediate focus on the 4 critical debugging features** that solve 80% of real problems. Foundation follows, advanced features are deferred.
