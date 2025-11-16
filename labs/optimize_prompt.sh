#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
HANDSHAKE="$ROOT/src/planloop/templates/prompts/core-v1/handshake.prompt.md"
PYTHONPATH="$ROOT:$ROOT/src"
AGENTS="copilot,openai,claude"

instructions=(
"Always close reported CI blocker signals via 'planloop alert --close' before editing tasks."
"After closing a blocker, rerun 'planloop status' and mention the new 'now.reason' before continuing."
"When encountering a signal, annotate 'signal-open' plus the blocker id in next_steps so we have traceability."
)

echo "Starting prompt optimization loop..."
for instruction in "${instructions[@]}"; do
  if grep -Fq "$instruction" "$HANDSHAKE"; then
    echo "Instruction already in prompt: $instruction"
  else
    printf "\n%s\n" "$instruction" >> "$HANDSHAKE"
    echo "Added instruction: $instruction"
  fi

  echo "Running lab with updated prompt..."
  output=$(cd "$ROOT" && PLANLOOP_LAB_INJECT_SIGNAL=1 PLANLOOP_LAB_SIGNAL_IGNORE=0 \
    PLANLOOP_LAB_COPILOT_CMD="bash labs/agents/mock_agent.sh" \
    PLANLOOP_LAB_OPENAI_CMD="bash labs/agents/mock_agent.sh" \
    PLANLOOP_LAB_CLAUDE_CMD="bash labs/agents/mock_agent.sh" \
    PYTHONPATH="$PYTHONPATH" \
    python3 labs/run_lab.py --scenario cli-basics --agents "$AGENTS")
  summary_line=$(echo "$output" | grep -F "Lab run complete:" | tail -n1)
  summary_path="$ROOT/${summary_line#Lab run complete: }"
  if [ ! -f "$summary_path" ]; then
    echo "Lab summary missing at $summary_path"
    exit 1
  fi
  echo "Lab run summary: $summary_path"
  compliance_pass=$(python3 - <<PY
import json, pathlib
path = pathlib.Path("$summary_path")
summary = json.loads(path.read_text())
print(all(agent["compliance"]["pass"] for agent in summary["agents"]))
PY
  )
  if [ "$compliance_pass" = "True" ]; then
    echo "All agents compliance pass with current instructions."
    exit 0
  fi
  echo "Compliance still failing after adding instruction: $instruction"
done

echo "Prompt optimization loop completed without achieving compliance across all agents."
exit 1
