#!/usr/bin/env bash
# Check for rate limit errors in recent test runs

set -euo pipefail

RESULTS_DIR="${1:-labs/results}"

echo "=== Checking for Rate Limit Errors ==="
echo

# Find recent runs with rate limit errors
rate_limit_runs=0
total_runs=0

for result_dir in "$RESULTS_DIR"/cli-basics-*/*/; do
  total_runs=$((total_runs + 1))
  
  # Check stderr and stdout for rate limit indicators  
  if [ -f "$result_dir/trace.log" ]; then
    if grep -q "rate_limit_exceeded" "$result_dir/trace.log"; then
      agent=$(basename "$(dirname "$result_dir")")
      run=$(basename "$(dirname "$(dirname "$result_dir")")")
      rate_limit_runs=$((rate_limit_runs + 1))
      
      echo "⚠️  $agent hit rate limit in $run"
      
      # Try to extract the actual error message
      if [ -f "$result_dir/stdout.txt" ]; then
        grep -i "usage limit\|rate limit\|quota" "$result_dir/stdout.txt" 2>/dev/null | head -1
      fi
      echo
    fi
  fi
done

echo "───────────────────────────────────────"
echo "Found $rate_limit_runs rate limit errors out of $total_runs agent runs"
echo

if [ $rate_limit_runs -gt 0 ]; then
  echo "💡 Tip: Check individual agent settings:"
  echo "   • Codex: https://chatgpt.com/codex/settings/usage"
  echo "   • Claude: https://claude.ai/settings/usage"  
  echo "   • Copilot: GitHub Copilot subscription"
  exit 1
else
  echo "✅ No rate limit errors detected"
  exit 0
fi
