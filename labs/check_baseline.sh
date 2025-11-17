#!/bin/bash
# Baseline regression checker
# Ensures Copilot performance doesn't degrade when optimizing other agents

set -e

BASELINE_PASS_RATE=41.8
BASELINE_AVG_SCORE=35.3
REGRESSION_THRESHOLD=5.0  # Alert if pass rate drops more than 5%

echo "=== Checking Copilot Baseline ==="

# Get current metrics (handle any copilot:* key)
CURRENT=$(python3 -c "
import json
with open('labs/metrics.json') as f:
    data = json.load(f)
    # Find any copilot key
    copilot = {}
    for key, val in data['agents_by_model'].items():
        if key.startswith('copilot:'):
            copilot = val
            break
    print(f\"{copilot.get('pass_rate', 0) * 100:.1f} {copilot.get('avg_score', 0):.1f}\")
")

read CURRENT_PASS_RATE CURRENT_AVG_SCORE <<< "$CURRENT"

echo "Baseline: ${BASELINE_PASS_RATE}% pass rate, ${BASELINE_AVG_SCORE} avg score"
echo "Current:  ${CURRENT_PASS_RATE}% pass rate, ${CURRENT_AVG_SCORE} avg score"

# Check for regression
DIFF=$(python3 -c "print(${BASELINE_PASS_RATE} - ${CURRENT_PASS_RATE})")
REGRESSION=$(python3 -c "print('yes' if abs(${DIFF}) > ${REGRESSION_THRESHOLD} and ${DIFF} > 0 else 'no')")

if [ "$REGRESSION" = "yes" ]; then
    echo ""
    echo "⚠️  WARNING: Copilot performance regression detected!"
    echo "   Pass rate dropped by ${DIFF}% (threshold: ${REGRESSION_THRESHOLD}%)"
    echo ""
    echo "Action needed:"
    echo "  1. Review recent prompt changes"
    echo "  2. Check if changes are Claude-specific or affect all agents"
    echo "  3. Consider agent-specific prompts if needed"
    echo ""
    exit 1
else
    CHANGE=$(python3 -c "import sys; diff=${DIFF}; sys.stdout.write('↓' if diff > 0 else '↑' if diff < 0 else '→')")
    echo ""
    echo "✅ No significant regression detected ${CHANGE}"
    exit 0
fi
