# Dev Mode Implementation Summary

**Status:** Ready for implementation  
**Last Updated:** 2025-11-18

---

## 📋 Documents

1. **Main Plan** (`dev-mode-observability-plan.md`) - Comprehensive specification
2. **Quick Reference** (`dev-mode-quick-reference.md`) - Implementation checklist & examples
3. **Debugging Analysis** (`../tmp/debugging-scenarios-analysis.md`) - User stories & justification

---

## 🎯 The 4 Critical Features (80% Impact)

Based on analyzing 10 common debugging scenarios, these 4 features solve 8 out of 10 problems:

### 1. ⭐⭐⭐⭐⭐ Error Context Capture
- **Solves:** 4/10 scenarios (crashes, corruption, desync, cascading failures)
- **File:** `src/planloop/dev_mode/error_context.py`
- **What:** Decorator that captures local variables, state snapshot, stack trace on error
- **Effort:** Medium

### 2. ⭐⭐⭐⭐⭐ Lock Operation Logging
- **Solves:** 2/10 scenarios (race conditions, deadlocks)
- **File:** `src/planloop/core/lock.py` (enhancement)
- **What:** Log every lock request/acquire/release with timing
- **Effort:** Low

### 3. ⭐⭐⭐⭐ Performance Spans
- **Solves:** 2/10 scenarios (performance degradation, rate limiting)
- **File:** `src/planloop/dev_mode/spans.py`
- **What:** Break down operation timing (LLM, I/O, parsing)
- **Effort:** Medium

### 4. ⭐⭐⭐⭐ Trace ID Linking
- **Solves:** 2/10 scenarios (crashes, cascading failures)
- **File:** `src/planloop/dev_mode/observability.py`
- **What:** Automatic linking error → LLM → diff via trace_id
- **Effort:** Low

**Total Effort:** 2-3 days for experienced developer

---

## 📦 What Gets Created

### Code Structure
```
src/planloop/
└── dev_mode/              # New module
    ├── __init__.py
    ├── manager.py         # Dev mode on/off/dogfood
    ├── observability.py   # Trace IDs, logging
    ├── error_context.py   # ⭐ Critical #1
    ├── spans.py           # ⭐ Critical #3
    └── recorder.py        # LLM transcripts, diffs
```

### Data Files
```
~/.planloop/sessions/<id>/logs/
├── planloop.jsonl              # All events (includes locks)
├── errors/                     # ⭐ Error reports
│   ├── {trace_id}_error.json
│   └── {trace_id}_state.json
├── llm_transcripts/
│   └── {trace_id}_llm.json
├── traces/                     # ⭐ Performance spans
│   └── {trace_id}.json
├── diffs/
│   ├── {trace_id}_pre.json
│   └── {trace_id}_post.json
└── performance.jsonl
```

---

## ✅ Definition of Done

**Phase 1A complete when:**

1. ✅ Trigger error → `logs/errors/{trace_id}_error.json` has full context
2. ✅ Run concurrent operations → lock events logged in JSONL
3. ✅ Run any command → `logs/traces/{trace_id}.json` has span breakdown
4. ✅ `planloop dev trace <trace_id>` shows linked error, LLM, spans

**Test:**
```bash
# Setup
planloop dev dogfood

# Test 1: Error context
planloop update --session test-invalid  # Force error
cat ~/.planloop/sessions/test-invalid/logs/errors/*.json

# Test 2: Lock logging
planloop update --session test & planloop update --session test &
grep "lock_" ~/.planloop/sessions/test/logs/planloop.jsonl

# Test 3: Performance spans
planloop update --session test
cat ~/.planloop/sessions/test/logs/traces/*.json

# Test 4: Trace linking
TRACE_ID=$(jq -r '.trace_id' ~/.planloop/sessions/test/logs/errors/*.json | head -1)
planloop dev trace $TRACE_ID --session test
```

---

## 🚀 Implementation Order

### Week 1: Critical Features (Phase 1A)
1. Day 1-2: Trace ID infrastructure + Error context capture
2. Day 3: Lock logging
3. Day 4: Performance spans
4. Day 5: Integration testing + polish

### Week 2: Foundation (Phase 1B)
- Dev mode management
- LLM transcript recording
- State diff tracking
- CLI export commands

### Week 3-4: API & Web UI (Phase 2-3)
- FastAPI endpoints
- Next.js dashboard
- Simple table-based UI

### Future: Low Priority (Phase 4)
- Comparison tool
- Validation logging
- Rate limiting metrics
- Memory profiling
- Advanced visualizations

---

## 💡 Key Design Decisions

1. **Web-first visualization** - No fancy terminal UIs, keep CLI simple
2. **Data-first approach** - Capture everything, visualize later
3. **Trace ID as linking key** - All events share trace_id for correlation
4. **JSON/JSONL output** - Machine-readable, scriptable
5. **Hot reload via editable install** - Fast iteration during self-development

---

## 📊 Expected Impact

**Before:**
- Developer triggers bug
- Adds print statements
- Re-runs, collects logs manually
- Spends 2-4 hours correlating data
- Eventually finds root cause

**After (with 4 critical features):**
- Developer triggers bug
- Error auto-captured with full context
- Runs `planloop dev trace <trace_id>`
- Sees: error, LLM call, performance breakdown, state
- Finds root cause in 5-15 minutes

**Time Saved:** 75-90% reduction in debugging time for captured scenarios

---

## 🎯 Success Stories (Expected)

Based on user story analysis:

- **Sarah (race condition):** Lock logs show exact sequence, finds bug in 30 min instead of 3 hours
- **Emma (AttributeError):** Error context shows LLM returned invalid task_id, fixed in 15 min instead of 2 hours
- **Lisa (performance):** Span breakdown shows state.json is 10MB, optimizes immediately
- **Jake (rate limiting):** Lock/LLM logs show request pattern, adds proper delays
- **Priya (deadlock):** Lock timeline reveals circular wait, fixes queue logic

---

## 📚 References

- **Main spec:** `docs/dev-mode-observability-plan.md`
- **Quick reference:** `docs/dev-mode-quick-reference.md`
- **Analysis:** `tmp/debugging-scenarios-analysis.md`
- **Existing code:**
  - Lock system: `src/planloop/core/lock.py`
  - Logging: `src/planloop/logging_utils.py`
  - LLM client: `src/planloop/core/llm_client.py`

---

**Ready to implement!** Start with Phase 1A - the 4 critical features that solve 80% of problems.
# Dev Mode Quick Reference

**Last Updated:** 2025-11-18

---

## 🎯 Implementation Checklist

### Phase 1A: Critical Features (IMPLEMENT FIRST)

- [ ] **Error Context Capture** (`src/planloop/dev_mode/error_context.py`)
  - Decorator: `@capture_error_context`
  - Captures: local vars, state snapshot, stack trace, LLM link
  - Output: `logs/errors/{trace_id}_error.json`

- [ ] **Lock Operation Logging** (`src/planloop/core/lock.py` enhancement)
  - Log: lock_requested, lock_acquired, lock_released
  - Track: wait time, hold time
  - Output: JSONL entries in `logs/planloop.jsonl`

- [ ] **Performance Spans** (`src/planloop/dev_mode/spans.py`)
  - Context manager: `with trace_span("operation_name"):`
  - Tracks: LLM, file I/O, parsing, business logic
  - Output: `logs/traces/{trace_id}.json`

- [ ] **Trace ID Linking** (`src/planloop/dev_mode/observability.py`)
  - Context var: `get_current_trace_id()`
  - Propagates through: logs, errors, LLM calls, diffs
  - Enables: automatic correlation of all events

### Phase 1B: Foundation

- [ ] Dev mode management (on/off/status/dogfood)
- [ ] Structured JSONL logging
- [ ] LLM transcript recording
- [ ] State diff tracking
- [ ] Basic performance metrics

### Phase 2-3: API & Web UI

- [ ] FastAPI endpoints for data access
- [ ] Next.js dashboard (sessions table, detail view)
- [ ] Log/LLM/trace viewers

### Phase 4: Future Enhancements (LOW PRIORITY)

- [ ] Comparison tool for runs
- [ ] Data validation logging
- [ ] Rate limiting metrics
- [ ] Memory profiling
- [ ] Deadlock detection
- [ ] Advanced visualizations

---

## 📝 File Locations

### Code to Create

```
src/planloop/
├── dev_mode/
│   ├── __init__.py
│   ├── manager.py              # Dev mode on/off/dogfood
│   ├── observability.py        # Logging, trace IDs
│   ├── error_context.py        # ⭐ Critical: Error capture
│   ├── spans.py                # ⭐ Critical: Performance spans
│   └── recorder.py             # LLM transcripts, diffs
└── core/
    └── lock.py                  # ⭐ Critical: Add lock logging
```

### Data Structure

```
~/.planloop/
├── .dev_mode                    # State marker
├── .dev_mode.json               # Extended state
└── sessions/<id>/
    └── logs/
        ├── planloop.jsonl       # Structured logs (all events)
        ├── errors/              # ⭐ Error reports
        │   ├── {trace_id}_error.json
        │   └── {trace_id}_state.json
        ├── llm_transcripts/     # LLM API calls
        │   └── {trace_id}_llm.json
        ├── traces/              # ⭐ Performance spans
        │   └── {trace_id}.json
        ├── diffs/               # State changes
        │   ├── {trace_id}_pre.json
        │   └── {trace_id}_post.json
        └── performance.jsonl    # Metrics
```

---

## 🔍 Debugging Workflow Examples

### Example 1: Error Occurred

```bash
# Error happens with trace_id: tr_20251118_abc123

# View full error context
planloop dev errors show tr_20251118_abc123

# Output shows:
# - Local variables at crash point
# - State snapshot
# - Stack trace with values
# - Link to LLM transcript

# Automatically find related data:
ls ~/.planloop/sessions/honk-xyz/logs/errors/tr_20251118_abc123_*
ls ~/.planloop/sessions/honk-xyz/logs/llm_transcripts/tr_20251118_abc123_*
ls ~/.planloop/sessions/honk-xyz/logs/traces/tr_20251118_abc123.json
```

### Example 2: Performance Issue

```bash
# Check what's slow
planloop dev perf --session honk-xyz

# Shows all operations with total time

# Drill into specific operation
planloop dev perf show tr_20251118_abc123

# Output shows span breakdown:
# - load_state: 12ms
# - llm_suggest: 2300ms  ← BOTTLENECK
# - parse_response: 5ms
# - save_state: 34ms
```

### Example 3: Race Condition

```bash
# Check lock operations
planloop dev locks --session honk-xyz

# Shows timeline:
# tr_abc: lock_requested (update) 08:00:00.000
# tr_def: lock_requested (update) 08:00:00.005
# tr_abc: lock_acquired (wait: 0ms) 08:00:00.001
# tr_def: lock_acquired (wait: 2344ms) 08:00:02.350
# tr_abc: lock_released (hold: 2340ms) 08:00:02.345
# tr_def: lock_released (hold: 1230ms) 08:00:03.580

# Clearly shows: tr_abc acquired first, tr_def waited 2.3s
```

---

## 💡 Key Implementation Notes

### Error Context Capture

**Usage:**
```python
from planloop.dev_mode.error_context import capture_error_context

@capture_error_context(session_dir)
def update_session(...):
    # Any error here gets full context
    ...
```

**What it captures:**
- `func.__code__.co_varnames` → local variables
- `traceback.extract_tb()` → stack trace
- `state.json` content → state snapshot
- Links via `trace_id` → finds LLM transcript automatically

### Performance Spans

**Usage:**
```python
from planloop.dev_mode.spans import trace_span

with trace_span("llm_call", provider="anthropic"):
    result = llm.generate(...)

with trace_span("save_state"):
    save_session_state(...)
```

**Automatic tracking:**
- Start time, end time, duration
- Nesting (parent/child spans)
- Metadata (provider, model, etc.)

### Trace ID Propagation

**Usage:**
```python
from planloop.dev_mode.observability import start_operation_trace

# At CLI entry point
trace_id = start_operation_trace("update")

# All subsequent code automatically uses this trace_id:
# - Logs
# - Errors
# - LLM transcripts
# - Performance spans
# - State diffs
```

**Benefit:** No need to pass trace_id everywhere - it's in thread-local context.

---

## 📊 Success Criteria

**Phase 1A is complete when:**

1. ✅ Run `planloop update --session test` and trigger an error
   - Check: `logs/errors/{trace_id}_error.json` exists with full context
   
2. ✅ Run two concurrent updates
   - Check: `logs/planloop.jsonl` has lock_requested, lock_acquired, lock_released events
   
3. ✅ Run any operation
   - Check: `logs/traces/{trace_id}.json` has span breakdown
   
4. ✅ Trigger error, then run:
   ```bash
   planloop dev trace <trace_id> --session test
   ```
   - Check: Shows linked error, LLM transcript, performance spans

**When these 4 work, 80% of debugging is solved.**

---

## 🔗 References

- Full plan: `docs/dev-mode-observability-plan.md`
- Debugging scenarios: `tmp/debugging-scenarios-analysis.md` (if kept)
- Existing code:
  - `src/planloop/logging_utils.py` - Current logging
  - `src/planloop/core/lock.py` - Lock implementation
  - `src/planloop/core/llm_client.py` - LLM client

---

**Remember:** Implement Phase 1A first. Don't get distracted by lower-priority features until the critical 4 are working.
