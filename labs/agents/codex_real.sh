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
# v0.2.0: Directive approach (learning: conversational hurt performance)
prompt=${PLANLOOP_LAB_AGENT_PROMPT:-"You are testing planloop workflow compliance. Your goal: Complete ALL tasks and handle ALL blockers.

**CRITICAL: Run 'planloop status' after EVERY action**
After 'planloop update' → Run status
After 'planloop alert --close' → Run status
NO EXCEPTIONS.

**WORKFLOW LOOP - Repeat until all tasks are DONE:**

1. START: Run 'planloop status --session $session --json'

2. READ 'now.reason' from status output:
   - If 'ci_blocker' or 'lint_blocker': Go to step 3
   - If 'task': Go to step 4
   - If 'waiting_on_lock' or 'deadlocked': STOP
   - If 'completed': STOP (success!)

3. BLOCKER HANDLING:
   a) Get blocker ID from 'now.blocker_id'
   b) Run: planloop alert --close --id <blocker-id>
   c) **CRITICAL**: Run 'planloop status --session $session --json' immediately
   d) Verify blocker cleared, go to step 2

4. TASK HANDLING:
   a) Get task ID from 'now.task_id'
   
   b) Mark IN_PROGRESS:
      echo '{\"tasks\": [{\"id\": TASK_ID, \"status\": \"IN_PROGRESS\"}]}' > payload.json
      planloop update --session $session --file payload.json
   
   c) **CRITICAL**: Run 'planloop status --session $session --json'
   
   d) Mark DONE:
      echo '{\"tasks\": [{\"id\": TASK_ID, \"status\": \"DONE\"}]}' > payload.json
      planloop update --session $session --file payload.json
   
   e) **CRITICAL**: Run 'planloop status --session $session --json'
   
   f) Go to step 1

**SUCCESS CRITERIA:**
- ALL tasks have status='DONE'
- Status called after EVERY update and alert close
- NO active blockers
- Final now.reason='completed'

**REMEMBER: The #1 failure is forgetting status after actions. Always verify your changes worked.**"} 

log_trace "run-start" "agent=codex workspace=$workspace session=$session"

# Detect model from config or default
model=${CODEX_MODEL:-"gpt-4"}  # Default to gpt-4
log_trace "agent-config" "model=$model"

# Create temp output files
codex_stdout="$trace_dir/codex_stdout.txt"
codex_stderr="$trace_dir/codex_stderr.txt"

# Run Codex CLI with appropriate flags
# Adjust based on actual codex CLI syntax when available
cd "$workspace"

echo "Running: codex -p <prompt> --model $model"

# Placeholder for actual codex command
# This will need to be updated based on actual Codex CLI syntax
# For now, using a similar pattern to other agents
if command -v codex &> /dev/null; then
    codex -p "$prompt" \
      --model "$model" \
      > "$codex_stdout" 2> "$codex_stderr" || {
        exit_code=$?
        log_trace "agent-error" "exit_code=$exit_code"
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
