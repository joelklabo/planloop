#!/bin/bash
# Safe optimization workflow with baseline protection
# Usage: ./labs/optimize_safely.sh <agent> <iterations>

set -e

AGENT=${1:-claude}
ITERATIONS=${2:-30}

echo "=== Safe Optimization Workflow ==="
echo "Agent: $AGENT"
echo "Iterations: $ITERATIONS"
echo ""

# Step 1: Check current baseline
echo "📊 Step 1: Checking Copilot baseline..."
./labs/check_baseline.sh
echo ""

# Step 2: Snapshot current metrics
echo "💾 Step 2: Snapshotting current metrics..."
cp labs/metrics.json tmp/metrics_before_${AGENT}_optimization.json
echo "Saved to tmp/metrics_before_${AGENT}_optimization.json"
echo ""

# Step 3: Run optimization iterations
echo "🔬 Step 3: Running $ITERATIONS iterations for $AGENT..."
./labs/run_iterations.sh $ITERATIONS cli-basics $AGENT
echo ""

# Step 4: Check for Copilot regression
echo "🔍 Step 4: Checking for Copilot regression..."
if ./labs/check_baseline.sh; then
    echo ""
    echo "✅ Optimization complete - no Copilot regression detected"
    
    # Show improvement for target agent
    echo ""
    echo "📈 $AGENT results:"
    python3 -c "
import json
with open('labs/metrics.json') as f:
    data = json.load(f)
    for key, val in data['agents_by_model'].items():
        if '$AGENT' in key.lower():
            print(f\"  {key}: {val['pass_rate']*100:.1f}% pass rate, {val['avg_score']:.1f} avg score\")
"
else
    echo ""
    echo "⚠️  Copilot regression detected!"
    echo ""
    echo "Options:"
    echo "  1. Revert prompt changes"
    echo "  2. Create agent-specific prompts"
    echo "  3. Find common patterns that work for both agents"
    echo ""
    echo "Previous metrics saved in: tmp/metrics_before_${AGENT}_optimization.json"
    exit 1
fi
