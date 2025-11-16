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
# This should align with ~/.planloop/prompts/core-v1/handshake.prompt.md
prompt=${PLANLOOP_LAB_AGENT_PROMPT:-"You are testing planloop workflow compliance. Follow these steps EXACTLY:

STEP 1: Run 'planloop status --session $session --json' to see current state

STEP 2: Check 'now.reason' in the status output:
- If it's a blocker (ci_blocker, lint_blocker): Close it with 'planloop alert --close --id <signal-id>'
- If waiting_on_lock: Stop here
- If deadlocked: Stop here
- If completed: Stop here  
- If task: Continue to step 3

STEP 3: After closing ANY blocker, MUST rerun 'planloop status' to verify it's cleared

STEP 4: Create a JSON payload file to update the referenced task to IN_PROGRESS:
{
  \"tasks\": [{\"id\": <task-id>, \"status\": \"IN_PROGRESS\"}],
  \"context_notes\": [\"Started working on this task\"],
  \"final_summary\": \"Updated task <id> to IN_PROGRESS\"
}

STEP 5: Run 'planloop update --session $session --file payload.json'

STEP 6: ALWAYS run 'planloop status --session $session --json' after updating to verify

STEP 7: If more TODO tasks exist, repeat from step 4 for the next task

Be systematic. Follow ALL steps."}

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
