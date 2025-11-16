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
prompt=${PLANLOOP_LAB_AGENT_PROMPT:-"You are working with planloop, a CI-aware task management system. Follow these steps:

1. Run 'planloop status --session $session --json' to see the current state
2. Check the 'now.reason' field - if it's a blocker (ci_blocker, lint_blocker, etc.), close it with 'planloop alert --close --id <signal-id>' before proceeding
3. After closing any blocker, rerun 'planloop status --session $session --json' to verify it's cleared
4. When now.reason is 'task', update the referenced task to IN_PROGRESS using 'planloop update --session $session --file <payload.json>'
5. After updating, run 'planloop status --session $session --json' again to verify
6. If there are more tasks, continue autonomously until all tasks are DONE

Be methodical and follow the workflow exactly."}

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
