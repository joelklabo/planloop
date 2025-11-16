#!/usr/bin/env bash
# Shared trace logging utilities for real agent adapters

log_trace() {
  local step=$1
  local detail=$2
  local trace_log=${PLANLOOP_LAB_RESULTS}/${PLANLOOP_LAB_AGENT_NAME}/trace.log
  mkdir -p "$(dirname "$trace_log")"
  printf '%s\t%s\t%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$step" "$detail" >>"$trace_log"
}

read_now_reason() {
  local status_file=$1
  if [ -f "$status_file" ]; then
    python3 - <<PY
import json
from pathlib import Path
payload = json.loads(Path("$status_file").read_text())
print(payload.get("now", {}).get("reason", "unknown"))
PY
  else
    echo "missing"
  fi
}

count_tasks_by_status() {
  local status_file=$1
  local target_status=$2
  if [ -f "$status_file" ]; then
    python3 - <<PY
import json
from pathlib import Path
payload = json.loads(Path("$status_file").read_text())
tasks = payload.get("tasks", [])
count = sum(1 for t in tasks if t.get("status") == "$target_status")
print(count)
PY
  else
    echo "0"
  fi
}

extract_model_from_output() {
  local output_file=$1
  # Try to find model information in agent output
  # Format: "Using model: gpt-4o" or similar
  if [ -f "$output_file" ]; then
    grep -i "model" "$output_file" | head -1 | sed 's/.*model[: ]*\([a-zA-Z0-9.-]*\).*/\1/' || echo "unknown"
  else
    echo "unknown"
  fi
}
