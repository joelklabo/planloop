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
# Load prompt from file to avoid bash escaping issues
PROMPT_FILE="$SCRIPT_DIR/../prompts/copilot-v0.3.1.txt"
if [ -n "${PLANLOOP_LAB_AGENT_PROMPT:-}" ]; then
  prompt="$PLANLOOP_LAB_AGENT_PROMPT"
elif [ -f "$PROMPT_FILE" ]; then
  # Read prompt and substitute $SESSION with actual session ID
  prompt=$(sed "s/\$SESSION/$session/g" "$PROMPT_FILE")
else
  echo "Error: Prompt file not found: $PROMPT_FILE"
  exit 1
fi

log_trace "run-start" "agent=copilot workspace=$workspace session=$session"

# Detect model from config or default
# Available models: claude-sonnet-4.5, claude-sonnet-4, claude-haiku-4.5, gpt-5, gpt-5.1, gpt-5.1-codex-mini, gpt-5.1-codex
model=${COPILOT_MODEL:-"gpt-5"}  # Default to gpt-5
log_trace "agent-config" "model=$model"

# Create temp output files
copilot_stdout="$trace_dir/copilot_stdout.txt"
copilot_stderr="$trace_dir/copilot_stderr.txt"
copilot_log_dir="$trace_dir/copilot_logs"
mkdir -p "$copilot_log_dir"

# Run Copilot CLI with appropriate flags
# --allow-all-tools: Required for non-interactive execution
# --allow-all-paths: Disable path verification
# --model: Specify model if available
# --log-level debug: Enable debug logging for troubleshooting
# --log-dir: Save logs to trace directory
# NOTE: --no-color causes silent exit code 1 failure in v0.0.358
cd "$workspace"

echo "Running: copilot -p <prompt> --allow-all-tools --allow-all-paths --model $model --log-level debug --log-dir $copilot_log_dir"

# Copilot v0.0.358 requires TTY-like behavior - direct redirection causes exit 1
# Use tee to capture output while maintaining terminal-like output
copilot -p "$prompt" \
  --allow-all-tools \
  --allow-all-paths \
  --model "$model" \
  --log-level debug \
  --log-dir "$copilot_log_dir" \
  2>&1 | tee "$copilot_stdout" || {
    exit_code=$?
    log_trace "agent-error" "exit_code=$exit_code"
    echo "Copilot execution failed with exit code $exit_code"
    cat "$copilot_stdout"
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
