#!/bin/bash
# Update baseline configuration
# Usage: ./labs/update_baseline.sh <agent> [--auto-detect]

set -e

AGENT=${1:-copilot}
AUTO_DETECT=${2}

if [ "$AUTO_DETECT" = "--auto-detect" ]; then
    echo "=== Auto-detecting current performance for $AGENT ==="
    
    # Get current metrics from metrics.json
    CURRENT=$(python3 -c "
import json
import sys
with open('labs/metrics.json') as f:
    data = json.load(f)
    found = False
    for key, val in data['agents_by_model'].items():
        if '$AGENT' in key.lower():
            print(f\"{val['pass_rate'] * 100:.1f} {val['avg_score']:.1f}\")
            found = True
            break
    if not found:
        print('ERROR: Agent $AGENT not found in metrics.json', file=sys.stderr)
        sys.exit(1)
")
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to detect metrics for $AGENT"
        echo "Make sure you have run lab tests recently."
        exit 1
    fi
    
    read PASS_RATE AVG_SCORE <<< "$CURRENT"
    
    echo "Detected performance:"
    echo "  Pass rate: ${PASS_RATE}%"
    echo "  Avg score: ${AVG_SCORE}"
    echo ""
    read -p "Update baseline to these values? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 0
    fi
else
    echo "=== Manual baseline update for $AGENT ==="
    echo "Enter new values:"
    read -p "Pass rate (0-100): " PASS_RATE
    read -p "Avg score (0-100): " AVG_SCORE
fi

# Get prompt version from user
read -p "Prompt version (e.g., v0.3.2): " VERSION
if [ -z "$VERSION" ]; then
    echo "Error: Version required"
    exit 1
fi

# Get notes
read -p "Notes (optional): " NOTES

# Update baseline.json
echo "Updating labs/baseline.json..."
python3 << EOF
import json
from datetime import datetime

with open('labs/baseline.json') as f:
    data = json.load(f)

agent = '$AGENT'
data[agent]['pass_rate'] = float('$PASS_RATE')
data[agent]['avg_score'] = float('$AVG_SCORE')
data[agent]['version'] = '$VERSION'
data[agent]['last_updated'] = datetime.now().strftime('%Y-%m-%d')
if '$NOTES':
    data[agent]['notes'] = '$NOTES'

with open('labs/baseline.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"✅ Updated {agent} baseline:")
print(f"  Pass rate: {data[agent]['pass_rate']}%")
print(f"  Avg score: {data[agent]['avg_score']}")
print(f"  Version: {data[agent]['version']}")
EOF

echo ""
echo "✅ Baseline updated successfully"
echo ""
echo "Next steps:"
echo "  1. Review the changes: git diff labs/baseline.json"
echo "  2. Commit the new baseline: git add labs/baseline.json"
echo "  3. Include in your prompt optimization commit"
