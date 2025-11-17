#!/usr/bin/env bash
# Real Claude CLI adapter with trace instrumentation

set -euo pipefail

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/trace_utils.sh"

# Environment setup
session=${PLANLOOP_SESSION:?}
workspace=${PLANLOOP_LAB_WORKSPACE:?}
agent_name=${PLANLOOP_LAB_AGENT_NAME:-claude}
trace_dir=${PLANLOOP_LAB_RESULTS:?}/$agent_name
mkdir -p "$trace_dir"

# Prompt for the agent - guide it through the planloop workflow
# v0.3.2: MAXIMUM emphasis on status-after for Claude (addresses 85% of failures)
prompt=${PLANLOOP_LAB_AGENT_PROMPT:-"You are testing planloop workflow compliance. Your goal: Complete ALL tasks and handle ALL blockers.

**CRITICAL RULE #1: ALWAYS RUN STATUS AFTER EVERY ACTION**
After EVERY 'planloop update' → MUST run 'planloop status'
After EVERY 'planloop alert --close' → MUST run 'planloop status'
NO EXCEPTIONS. This is the #1 requirement.

**WORKFLOW LOOP - Repeat until all tasks are DONE:**

1. ALWAYS START: Run 'planloop status --session $session --json'

2. READ 'now.reason' from status output:
   - If 'ci_blocker' or 'lint_blocker': Go to BLOCKER HANDLING
   - If 'task': Go to TASK HANDLING
   - If 'waiting_on_lock' or 'deadlocked': STOP
   - If 'completed': STOP

3. BLOCKER HANDLING (if now.reason contains blocker):
   a) Close signal: 'planloop alert --close --id <signal-id>' (get id from 'now.blocker_id')
   b) ⚠️ MANDATORY: Run 'planloop status --session $session --json' immediately
   c) Verify blocker cleared, then go back to step 2

4. TASK HANDLING (if now.reason is 'task'):
   a) Get task id from 'now.task_id' in status output
   b) Write payload.json: {\"tasks\": [{\"id\": <task-id>, \"status\": \"IN_PROGRESS\"}]}
   c) Run 'planloop update --session $session --file payload.json'
   d) ⚠️ MANDATORY: Run 'planloop status --session $session --json'
   e) Write payload.json: {\"tasks\": [{\"id\": <task-id>, \"status\": \"DONE\"}]}
   f) Run 'planloop update --session $session --file payload.json'
   g) ⚠️ MANDATORY: Run 'planloop status --session $session --json'
   h) Go back to step 1

5. CHECK COMPLETION: After each status, check if ANY tasks remain TODO or IN_PROGRESS
   - If yes: Continue loop from step 1
   - If no: All done!

REMEMBER:
✓ Status after EVERY update (steps 4d and 4g)
✓ Status after closing ANY signal (step 3b)
✓ Keep going until ALL tasks are DONE
✓ Don't stop early - check completion after every status"}

log_trace "run-start" "agent=claude workspace=$workspace session=$session"

# Detect model from config or default
# Claude aliases: 'sonnet', 'opus', or full names like 'claude-sonnet-4-5-20250929'
model=${CLAUDE_MODEL:-"sonnet"}  # Default to latest sonnet
log_trace "agent-config" "model=$model"

# Create temp output files
claude_stdout="$trace_dir/claude_stdout.txt"
claude_stderr="$trace_dir/claude_stderr.txt"

# Run Claude CLI with appropriate flags
# --print: Non-interactive mode, print response and exit
# --allowedTools "Bash": Only allow bash commands (safer than full permissions)
# --model: Specify model
cd "$workspace"

echo "Running: claude -p <prompt> --print --allowedTools \"Bash\" --model $model"

claude -p "$prompt" \
  --print \
  --allowedTools "Bash" \
  --model "$model" \
  > "$claude_stdout" 2> "$claude_stderr" || {
    exit_code=$?
    log_trace "agent-error" "exit_code=$exit_code"
    
    # Check for common error patterns
    if grep -qi "rate limit\|usage limit\|quota exceeded\|session limit" "$claude_stderr" "$claude_stdout" 2>/dev/null; then
      echo "⚠️  RATE LIMIT ERROR: Claude usage limit reached" >&2
      log_trace "agent-error" "rate_limit_exceeded"
      cat "$claude_stderr"
      exit 2  # Distinct exit code for rate limits
    fi
    
    echo "Claude execution failed with exit code $exit_code"
    cat "$claude_stderr"
    exit $exit_code
}

# Parse output to generate trace entries
# Look for planloop command executions in the output

# Check for status calls
status_count=$(grep -c "planloop status" "$claude_stdout" || echo "0")
log_trace "commands-executed" "status_calls=$status_count"

# Try to detect actual workflow steps by looking at output
if grep -q "planloop status" "$claude_stdout"; then
  log_trace "status" "detected in output"
fi

if grep -q "planloop alert" "$claude_stdout"; then
  log_trace "alert" "signal handling detected"
fi

if grep -q "planloop update" "$claude_stdout"; then
  log_trace "update" "task update detected"
fi

# Final status check - see what state we ended in
if [ -f "$HOME/.planloop/sessions/$session/state.json" ]; then
  final_reason=$(read_now_reason "$HOME/.planloop/sessions/$session/state.json")
  done_count=$(count_tasks_by_status "$HOME/.planloop/sessions/$session/state.json" "DONE")
  total_count=$(python3 -c "import json; print(len(json.loads(open('$HOME/.planloop/sessions/$session/state.json').read())['tasks']))")
  
  log_trace "final-state" "reason=$final_reason done=$done_count/$total_count"
else
  log_trace "final-state" "session_state_not_found"
fi

log_trace "run-end" "status=completed"

echo "Claude agent run complete. Check $trace_dir/trace.log for details."
