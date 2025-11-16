#!/usr/bin/env bash
# Run multiple lab iterations and track performance improvements

set -euo pipefail

ITERATIONS=${1:-5}
SCENARIO=${2:-cli-basics}
AGENTS=${3:-copilot,claude}

echo "=== Running $ITERATIONS iterations of $SCENARIO ==="
echo "Agents: $AGENTS"
echo ""

cd "$(dirname "$0")/.."
source .venv/bin/activate

for i in $(seq 1 $ITERATIONS); do
  echo "=== Iteration $i/$ITERATIONS ==="
  
  PLANLOOP_LAB_COPILOT_CMD="bash labs/agents/copilot_real.sh" \
  PLANLOOP_LAB_CLAUDE_CMD="bash labs/agents/claude_real.sh" \
  PLANLOOP_LAB_INJECT_SIGNAL=1 \
  PYTHONPATH=. python labs/run_lab.py --scenario "$SCENARIO" --agents "$AGENTS"
  
  echo ""
done

echo "=== Aggregating metrics ==="
PYTHONPATH=. python labs/aggregate_metrics.py

echo ""
echo "=== Generating visualization ==="
PYTHONPATH=. python labs/generate_viz.py

echo ""
echo "=== Done! ==="
echo "Check docs/agent-performance.md for results"
