# Multi-Agent Collaboration Setup Guide

This guide explains how to use planloop with multiple agents working in the same session.

## Overview

Planloop supports multiple agents collaborating on the same session through:
- **File-based locking** with queue fairness
- **Session persistence** across commands
- **Task-level coordination** via status updates
- **Lock queue visibility** for agent awareness

## Quick Start

### 1. Create a Shared Session

```bash
planloop sessions create \
  --name "feature-dev" \
  --title "Feature Development" \
  --project-root /path/to/project
```

### 2. Configure Each Agent

Each agent should use the same session ID:

```bash
export PLANLOOP_SESSION="feature-dev-20241118T..."
```

Or specify explicitly in commands:

```bash
planloop status --session feature-dev-20241118T...
```

### 3. Agent Coordination

Agents automatically coordinate through the lock system:

- **Lock acquisition**: First agent gets the lock
- **Queue fairness**: Other agents wait in FIFO order
- **Automatic release**: Lock released after state updates
- **Stall detection**: Detects and recovers from stalls

## Multi-Agent Patterns

### Pattern 1: Parallel Task Execution

Multiple agents work on different tasks simultaneously:

**Agent A**:
```bash
# Agent A works on task 1
planloop update --file update_task1.json
```

**Agent B**:
```bash
# Agent B works on task 2 (waits for lock)
planloop update --file update_task2.json
```

The lock system ensures safe concurrent access.

###  Pattern 2: Handoff Workflow

Agents pass work between each other:

1. Agent A completes task → marks DONE
2. Agent B checks status → sees task complete
3. Agent B starts next task automatically

### Pattern 3: Specialized Agents

Different agents handle different task types:

- **Test Agent**: Monitors `type: test` tasks
- **Documentation Agent**: Handles `type: chore` documentation
- **Implementation Agent**: Works on `type: feature` tasks

## Session Persistence

### Current Session Pointer

Planloop maintains a current session pointer at:
```
~/.planloop/current-session.txt
```

This allows commands without `--session` flag to use the active session:

```bash
# Set current session
planloop sessions switch feature-dev-20241118T...

# Now all commands use this session
planloop status
planloop update --file changes.json
```

### Switching Between Sessions

```bash
# List all sessions
planloop sessions list

# Switch to different session
planloop sessions switch other-session-id

# Check current session
planloop sessions current
```

## Lock Queue Management

### Viewing Lock Status

```bash
planloop status --json | jq '.lock_info, .lock_queue'
```

Output shows:
- **lock_info**: Current lock holder and entry ID
- **lock_queue**: Pending agents in FIFO order
- **position**: Your position in queue (if waiting)

### Understanding Queue Position

When multiple agents compete for the lock:

```json
{
  "lock_queue": {
    "pending": [
      {"entry_id": "abc123", "operation": "update"},
      {"entry_id": "def456", "operation": "update"}
    ],
    "position": 2
  }
}
```

Agent at position 1 is next to acquire the lock.

## Best Practices

### 1. Always Use TDD Workflow

Follow the TDD checklist for every task:
- ✓ Write test first
- ✓ Watch it FAIL (red)
- ✓ Implement to make it PASS (green)
- ✓ Refactor
- ✓ Commit

### 2. Small, Frequent Updates

Minimize lock hold time:
- Make atomic changes
- Commit often
- Release lock quickly

### 3. Check Status Before Starting

```bash
# Always check current state
planloop status --json

# Follow next_action guidance
jq '.next_action' status.json
```

### 4. Handle Lock Waits Gracefully

If waiting for lock:
- Continue with read-only operations
- Prepare changes offline
- Retry after delay

### 5. Use Transition Detection

Status response includes `transition_detected`:

```json
{
  "transition_detected": true,
  "completed_task_id": 5,
  "next_action": {
    "action": "continue",
    "task_id": 6
  }
}
```

This signals when to proceed to next task automatically.

## Troubleshooting

### Agent Stuck Waiting for Lock

**Problem**: Agent waiting indefinitely for lock

**Solution**:
```bash
# Check lock status
planloop debug --session SESSION_ID

# If lock is stale, check deadlock tracker
cat ~/.planloop/sessions/SESSION_ID/deadlock.json
```

### Session Out of Sync

**Problem**: Agent sees stale state

**Solution**:
```bash
# Reload session from disk
planloop sessions info --session SESSION_ID
```

### Multiple Current Sessions

**Problem**: Different agents using different sessions

**Solution**:
1. Agree on canonical session ID
2. All agents switch to same session:
   ```bash
   planloop sessions switch AGREED_SESSION_ID
   ```

## Configuration

### Per-Agent Configuration

Each agent can have custom config in `~/.planloop/config.yml`:

```yaml
# Agent-specific settings
safe_modes:
  update:
    dry_run: false
    no_plan_edit: false  # Allow structural changes
    strict: true         # Strict validation

history:
  enabled: true         # Enable snapshots

logging:
  level: INFO          # Adjust verbosity
```

### Session-Level Settings

Session configuration in `state.json`:
- `project_root`: Shared project path
- `prompts`: Shared prompt set
- `environment`: Runtime environment info

## Advanced: Custom Coordination

### Using Signals for Communication

Agents can use signals to communicate:

```bash
# Agent A raises signal
planloop alert \
  --type lint \
  --level warning \
  --title "Linting errors" \
  --detail "Fix before continuing"

# Agent B sees signal in status
planloop status --json | jq '.signals'

# Agent B resolves and closes
planloop alert --close SIGNAL_ID
```

### Task Dependencies

Use `depends_on` for task ordering:

```json
{
  "add_tasks": [
    {
      "title": "Implement feature",
      "type": "feature",
      "depends_on": []
    },
    {
      "title": "Add tests",
      "type": "test",
      "depends_on": [1]  // Waits for task 1
    }
  ]
}
```

## Example: Two-Agent Workflow

**Agent A (Implementation)**:
```bash
# Start session
planloop sessions create --name "api-dev" --title "API Development"

# Work on implementation
while true; do
  STATUS=$(planloop status --json)
  ACTION=$(echo $STATUS | jq -r '.next_action.action')
  
  if [ "$ACTION" = "continue" ]; then
    TASK_ID=$(echo $STATUS | jq -r '.next_action.task_id')
    # Implement task...
    planloop update --file task_${TASK_ID}_done.json
  else
    break
  fi
done
```

**Agent B (Testing)**:
```bash
# Join session
planloop sessions switch api-dev-20241118T...

# Monitor for implementation completion
while true; do
  STATUS=$(planloop status --json)
  IMPL_DONE=$(echo $STATUS | jq '.tasks[] | select(.type=="feature" and .status=="DONE")')
  
  if [ -n "$IMPL_DONE" ]; then
    # Add tests for completed implementations
    planloop suggest --focus tests/
  fi
  
  sleep 60
done
```

## Summary

Multi-agent collaboration with planloop:
- ✓ Safe concurrent access via locking
- ✓ Queue fairness prevents starvation
- ✓ Session persistence across commands
- ✓ Automatic transition detection
- ✓ Clear coordination signals

Follow the TDD workflow, check status frequently, and let the lock system handle coordination.
