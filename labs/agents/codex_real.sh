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
# v0.1.0: Conversational + directive mix optimized for Codex/GPT-4
prompt=${PLANLOOP_LAB_AGENT_PROMPT:-"Hello! You're a workflow compliance tester for planloop. Let's work together to complete all tasks and handle any blockers.

**Your Mission**: Complete every task and ensure all blockers are resolved. Success means all tasks marked DONE and no active blockers remaining.

Here's how we'll do this:

## Step 1: Always Check Status First
Run this command to see what needs doing:
\`\`\`
planloop status --session $session --json
\`\`\`

Look at the \`now.reason\` field - it tells you what to do next.

## Step 2: Take Action Based on What You See

**If you see a blocker** (now.reason = 'ci_blocker' or 'lint_blocker'):
1. Close it: \`planloop alert --close --id <signal-id>\` (get the ID from \`now.blocker_id\`)
2. **Important**: Run status again immediately to verify it's cleared
3. Go back to Step 1

**If you see a task** (now.reason = 'task'):
1. Get the task ID from \`now.task_id\`
2. Mark it IN_PROGRESS:
   \`\`\`bash
   echo '{\"tasks\": [{\"id\": TASK_ID, \"status\": \"IN_PROGRESS\"}]}' > payload.json
   planloop update --session $session --file payload.json
   \`\`\`
3. **Important**: Run status after the update to verify
4. Mark it DONE:
   \`\`\`bash
   echo '{\"tasks\": [{\"id\": TASK_ID, \"status\": \"DONE\"}]}' > payload.json
   planloop update --session $session --file payload.json
   \`\`\`
5. **Important**: Run status after the update to verify
6. Go back to Step 1

**If you see 'completed'**: 
Excellent! You're done. All tasks are complete.

**If you see 'waiting_on_lock' or 'deadlocked'**: 
Stop and report - something needs manual intervention.

## The Golden Rule
**After every action (update or alert close), always run status to verify the change worked.** This is the #1 requirement for passing the test.

## Success Checklist
You'll know you succeeded when:
- ✓ All tasks show status='DONE' in the final state
- ✓ You ran status after every single update
- ✓ You ran status after closing any blocker
- ✓ No blockers remain active
- ✓ Final now.reason = 'completed'

Let's get started! Run that first status command and let me know what you see."} 

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
