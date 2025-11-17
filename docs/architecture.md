# planloop Architecture

**Purpose**: Technical reference for planloop's design and implementation

---

## System Design

### Core Philosophy
planloop is a **CI-aware task loop** that keeps AI agents synchronized with a shared plan using file-based state and queue fairness.

**Key Principles**:
- File-based state (no database)
- Git-based history (optional)
- Multi-agent coordination via FIFO queue
- Fail-fast validation with rich error messages
- Read-only dashboards for monitoring

---

## State Management

### State Structure
Each session has:
- `state.json` - Canonical state (tasks, context, metadata, alerts)
- `PLAN.md` - Human-readable rendering of state
- `.lock` - Binary mutex for atomic operations
- `.lock_info` - Lock metadata (holder, operation, timestamp)
- `.lock_queue/` - Queue entries for waiting agents

### State Flow
```
Agent → planloop status --json
      ↓
Compute "now" (next action based on state)
      ↓
Agent decides action
      ↓
Agent → planloop update/alert
      ↓
Acquire lock → Validate → Write state → Release lock
      ↓
Regenerate PLAN.md
```

### Compute "now" Logic
The `compute_now` function determines what agents should do next:
1. Check for active blocker signals → `ci_blocker`, `lint_blocker`, etc.
2. Check lock status → `waiting_on_lock`, `deadlocked`
3. Find first TODO/IN_PROGRESS task → `task` with task_id
4. All done → `completed`

---

## Locking & Queue Fairness

### Problem
Simple binary locks allow starvation - one agent could repeatedly grab the lock while others wait indefinitely.

### Solution: FIFO Queue
**Queue Design** (implemented in v1.5):
1. Agent writes `.lock_queue/<uuid>.json` with request metadata:
   ```json
   {
     "agent": "pid:12345",
     "operation": "update",
     "requested_at": "2025-11-17T00:00:00Z",
     "timeout_ms": 300000
   }
   ```
2. Queue determines order - first entry = lock holder
3. Stale entries pruned via TTL (requested_at + timeout_ms)
4. `planloop status` shows queue position and pending agents

**Deadlock Detection**:
- `DeadlockTracker` watches queue head
- If same agent stalls at head for N cycles → emit `queue_stall` signal
- Agents handle stall signal same as CI blockers

**Telemetry**:
- Queue events logged to `logs/planloop.log`
- Status output includes queue depth and position
- Future: aggregated metrics via `planloop debug --logs`

---

## Session Management

### PLANLOOP_HOME
Default: `~/.planloop/`

Structure:
```
~/.planloop/
├── sessions/
│   ├── <session-id>/
│   │   ├── state.json
│   │   ├── PLAN.md
│   │   ├── .lock
│   │   ├── .lock_info
│   │   ├── .lock_queue/
│   │   └── .git/ (if history enabled)
│   └── index.json
├── prompts/
│   └── core-v1/
├── messages/
├── templates/
├── logs/
└── config.yml
```

### Session Lifecycle
1. **Create**: `planloop sessions create` → generate UUID, initialize state
2. **Use**: Set current pointer in `sessions/index.json`
3. **Update**: Agents modify via `planloop update --file payload.json`
4. **Archive**: History preserved in `.git/` if enabled
5. **Restore**: `planloop restore <sha>` to roll back

---

## Command System

### Core Commands
- **`status`** - Get current state and "now" recommendation
- **`update`** - Modify tasks/context (requires lock)
- **`alert`** - Open/close blocker signals
- **`describe`** - Get state schema and field docs

### Session Commands
- **`sessions create/list/info/set/unset`** - Manage sessions
- **`search`** - Find sessions by query
- **`templates`** - List reusable session templates
- **`reuse`** - Create session from template

### Safe Modes
Configured in `~/.planloop/config.yml`:
```yaml
safe_modes:
  update:
    dry_run: false        # Preview changes without writing
    no_plan_edit: false   # Only update task statuses
    strict: false         # Reject unknown fields
```

### History & Debugging
- **`snapshot`** - Save current state to git
- **`restore <sha>`** - Roll back to snapshot
- **`view`** - TUI dashboard (requires textual)
- **`web`** - Web dashboard (requires fastapi+uvicorn)

---

## Validation & Safety

### Input Validation
- Pydantic models with JSON schema
- Strict mode rejects unknown fields
- Dry-run mode previews changes
- Rich error messages with context

### State Invariants
- Enforced on every write
- Examples:
  - At most one task IN_PROGRESS per agent
  - Signal IDs must be unique
  - Task dependencies must form DAG (future)

### Failure Modes
- Lock acquisition timeout → `waiting_on_lock`
- Queue head stall → `queue_stall` signal
- Validation failure → descriptive error + exit 1
- Missing deps → suggest installation command

---

## Testing Infrastructure

### Selftests
`planloop selftest` creates temporary PLANLOOP_HOME and runs:
- Clean scenario (basic workflow)
- CI blocker scenario (signal handling)
- Dependency scenario (task ordering)

### Lab Testing
Real agent CLIs tested against scenarios:
- **cli-basics**: 2 tasks + 1 CI blocker
- Future: multi-signal-cascade, dependency-chain, full-plan-completion

**Evaluation**:
- 0-100 score based on compliance
- Pass = 100 (perfect workflow execution)
- Metrics: status usage, update correctness, signal handling

**See**: `lab-testing.md` for details

---

## Extensibility

### Adding Commands
1. Add function to `src/planloop/cli.py` with Typer decorator
2. Use shared helpers from `src/planloop/core/`
3. Add tests in `tests/`

### Adding Scenarios
1. Create `labs/scenarios/<name>.py`
2. Define setup, tasks, signal injection points
3. Register in evaluation system

### Prompt Customization
Edit prompts in `~/.planloop/prompts/core-v1/`:
- `handshake.prompt.md` - Initial instructions
- `goal.prompt.md` - Goal framing
- `summary.prompt.md` - Session summary
- `reuse_template.prompt.md` - Template usage

---

## Performance Considerations

### Scalability
- File-based state limits: ~1000 tasks per session recommended
- Lock queue: O(n) for queue operations (acceptable for <100 agents)
- Git history: grows linearly with snapshots (prune old commits)

### Optimization Opportunities
- Index tasks by status for faster lookup
- Cache computed "now" within lock hold
- Batch queue pruning
- Compress old snapshots

---

## Future Directions (v1.6+)

- Task dependency visualization
- Distributed locking (cross-machine coordination)
- Session analytics dashboard
- Lock queue tuning (adaptive timeouts)
- Performance profiling for large plans
- Multi-session orchestration
