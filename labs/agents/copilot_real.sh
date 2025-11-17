#!/usr/bin/env bash
# Real GitHub Copilot CLI adapter with trace instrumentation

set -euo pipefail

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/trace_utils.sh"

# Environment setup
session=${PLANLOOP_SESSION:?}
workspace=${PLANLOOP_LAB_WORKSPACE:?}
agent_name=${PLANLOOP_LAB_AGENT_NAME:-copilot}
trace_dir=${PLANLOOP_LAB_RESULTS:?}/$agent_name
mkdir -p "$trace_dir"

# Prompt for the agent - guide it through the planloop workflow
# v0.3.1: Enhanced to address top failure patterns (missing status-after, missing updates)
prompt=${PLANLOOP_LAB_AGENT_PROMPT:-"You are testing planloop workflow compliance. Your goal: Complete ALL tasks and handle ALL blockers.

**WORKFLOW LOOP - Repeat until all tasks are DONE:**

1. ALWAYS START: Run 'planloop status --session $session --json'

2. READ 'now.reason' from status output:
   - If 'ci_blocker' or 'lint_blocker': Go to BLOCKER HANDLING
   - If 'task': Go to TASK HANDLING
   - If 'waiting_on_lock' or 'deadlocked': STOP
   - If 'completed': STOP

3. BLOCKER HANDLING (if now.reason contains blocker):
   a) Close signal: 'planloop alert --close --id <signal-id>' (get id from 'now.blocker_id')
   b) CRITICAL: MUST run 'planloop status --session $session --json' again to verify blocker cleared
   c) Go back to step 2

4. TASK HANDLING (if now.reason is 'task'):
   a) Get task id from 'now.task_id' in status output
   b) Write payload.json with:
      {\"tasks\": [{\"id\": <task-id>, \"status\": \"IN_PROGRESS\"}]}
   c) Run 'planloop update --session $session --file payload.json'
   d) CRITICAL: MUST run 'planloop status --session $session --json' after EVERY update
   e) Write payload.json to mark DONE:
      {\"tasks\": [{\"id\": <task-id>, \"status\": \"DONE\"}]}
   f) Run 'planloop update --session $session --file payload.json'
   g) CRITICAL: MUST run 'planloop status --session $session --json' after update
   h) Go back to step 1

5. CHECK COMPLETION: After each status, check if ANY tasks remain TODO or IN_PROGRESS
   - If yes: Continue loop from step 1
   - If no: All done!

RULES:
- Run status AFTER closing ANY signal
- Run status AFTER ANY update
- Keep going until ALL tasks show status='DONE'
- Don't stop early"}

log_trace "run-start" "agent=copilot workspace=$workspace session=$session"

# Detect model from config or default
# Available models: claude-sonnet-4.5, claude-sonnet-4, claude-haiku-4.5, gpt-5, gpt-5.1, gpt-5.1-codex-mini, gpt-5.1-codex
model=${COPILOT_MODEL:-"gpt-5"}  # Default to gpt-5
log_trace "agent-config" "model=$model"

# Create temp output files
copilot_stdout="$trace_dir/copilot_stdout.txt"
copilot_stderr="$trace_dir/copilot_stderr.txt"

# Run Copilot CLI with appropriate flags
# --allow-all-tools: Required for non-interactive execution
# --allow-all-paths: Disable path verification
# --no-color: Clean output for parsing
# --model: Specify model if available
cd "$workspace"

echo "Running: copilot -p <prompt> --allow-all-tools --allow-all-paths --no-color --model $model"

copilot -p "$prompt" \
  --allow-all-tools \
  --allow-all-paths \
  --no-color \
  --model "$model" \
  > "$copilot_stdout" 2> "$copilot_stderr" || {
    exit_code=$?
    log_trace "agent-error" "exit_code=$exit_code"
    echo "Copilot execution failed with exit code $exit_code"
    cat "$copilot_stderr"
    exit $exit_code
}

# Parse output to generate trace entries
# Look for planloop command executions in the output

# Check for status calls
status_count=$(grep -c "planloop status" "$copilot_stdout" || echo "0")
log_trace "commands-executed" "status_calls=$status_count"

# Try to detect actual workflow steps by looking at output
if grep -q "planloop status" "$copilot_stdout"; then
  log_trace "status" "detected in output"
fi

if grep -q "planloop alert" "$copilot_stdout"; then
  log_trace "alert" "signal handling detected"
fi

if grep -q "planloop update" "$copilot_stdout"; then
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

echo "Copilot agent run complete. Check $trace_dir/trace.log for details."
