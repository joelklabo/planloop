#!/usr/bin/env bash
# Real Codex (OpenAI) CLI adapter with trace instrumentation

set -euo pipefail

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/trace_utils.sh"

# Environment setup
session=${PLANLOOP_SESSION:?}
workspace=${PLANLOOP_LAB_WORKSPACE:?}
agent_name=${PLANLOOP_LAB_AGENT_NAME:-codex}
trace_dir=${PLANLOOP_LAB_RESULTS:?}/$agent_name
mkdir -p "$trace_dir"

# Prompt for the agent - guide it through the planloop workflow  
# v0.3.0: Minimal/direct approach (research: "less is more" for Codex CLI)
prompt=${PLANLOOP_LAB_AGENT_PROMPT:-"Complete all tasks in the planloop workflow. Session: $session

Workflow:
1. Run: planloop status --session $session --json
2. Read now.reason field
3. If blocker: close it with planloop alert --close, then status
4. If task: update to IN_PROGRESS, status, update to DONE, status
5. Repeat until now.reason is 'completed'

Critical: Run status after every update and alert close."} 

log_trace "run-start" "agent=codex workspace=$workspace session=$session"

# Detect model from config or default
model=${CODEX_MODEL:-"gpt-4"}  # Default to gpt-4
log_trace "agent-config" "model=$model"

# Create temp output files
codex_stdout="$trace_dir/codex_stdout.txt"
codex_stderr="$trace_dir/codex_stderr.txt"

# Run Codex CLI with appropriate flags
cd "$workspace"

echo "Running: codex exec <prompt> --sandbox workspace-write --model $model"

# Use codex exec for non-interactive execution
# --sandbox workspace-write: Allow file writes in workspace
# --model: Specify model
if command -v codex &> /dev/null; then
    echo "$prompt" | codex exec - \
      --sandbox workspace-write \
      --model "$model" \
      > "$codex_stdout" 2> "$codex_stderr" || {
        exit_code=$?
        log_trace "agent-error" "exit_code=$exit_code"
        
        # Check for common error patterns
        if grep -qi "usage limit\|rate limit\|quota exceeded\|purchase more credits" "$codex_stderr" "$codex_stdout" 2>/dev/null; then
          echo "⚠️  RATE LIMIT ERROR: Codex usage limit reached" >&2
          log_trace "agent-error" "rate_limit_exceeded"
          cat "$codex_stderr"
          exit 2  # Distinct exit code for rate limits
        fi
        
        echo "Codex execution failed with exit code $exit_code"
        cat "$codex_stderr"
        exit $exit_code
    }
else
    echo "Error: codex command not found. Please install Codex CLI." >&2
    log_trace "agent-error" "codex_cli_not_installed"
    exit 127
fi

# Parse output to generate trace entries
status_count=$(grep -c "planloop status" "$codex_stdout" || echo "0")
log_trace "commands-executed" "status_calls=$status_count"

# Check for workflow steps
if grep -q "planloop status" "$codex_stdout"; then
  log_trace "status" "detected in output"
fi

if grep -q "planloop alert" "$codex_stdout"; then
  log_trace "alert" "signal handling detected"
fi

if grep -q "planloop update" "$codex_stdout"; then
  log_trace "update" "task update detected"
fi

# Final status check
if [ -f "$HOME/.planloop/sessions/$session/state.json" ]; then
  final_reason=$(read_now_reason "$HOME/.planloop/sessions/$session/state.json")
  done_count=$(count_tasks_by_status "$HOME/.planloop/sessions/$session/state.json" "DONE")
  total_count=$(python3 -c "import json; print(len(json.loads(open('$HOME/.planloop/sessions/$session/state.json').read())['tasks']))")
  
  log_trace "final-state" "reason=$final_reason done=$done_count/$total_count"
else
  log_trace "final-state" "session_state_not_found"
fi

log_trace "run-end" "status=completed"

echo "Codex agent run complete. Check $trace_dir/trace.log for details."
