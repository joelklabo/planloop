#!/usr/bin/env bash
set -euo pipefail

session=${PLANLOOP_SESSION:?}
workspace=${PLANLOOP_LAB_WORKSPACE:?}
agent_name=${PLANLOOP_LAB_AGENT_NAME:-mock}
trace_dir=${PLANLOOP_LAB_RESULTS:?}/$agent_name
mkdir -p "$trace_dir"
trace_log="$trace_dir/trace.log"

log_entry() {
  local step=$1
  local detail=$2
  printf '%s\t%s\t%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$step" "$detail" >>"$trace_log"
}

read_now_reason() {
  local file=$1
  if [ -f "$file" ]; then
    python3 - <<PY
import json
from pathlib import Path

payload = json.loads(Path("$file").read_text())
print(payload.get("now", {}).get("reason", "unknown"))
PY
  else
    echo "missing"
  fi
}

should_run_status=${PLANLOOP_LAB_SIMULATE_NO_STATUS:-0}
inject_signal=${PLANLOOP_LAB_INJECT_SIGNAL:-0}
ignore_signal=${PLANLOOP_LAB_SIGNAL_IGNORE:-0}
signal_id=${PLANLOOP_LAB_SIGNAL_ID:-ci-blocker-lab}
export PLANLOOP_LAB_SIGNAL_ID=$signal_id

handshake_body=$(python3 - <<PY
from planloop.core.prompts import load_prompt
print(load_prompt("core-v1", "handshake").body.lower())
PY
)
should_close_signal=0
should_status_after=0
if echo "$handshake_body" | grep -qi "close blocker"; then
  should_close_signal=1
fi
if echo "$handshake_body" | grep -qi "alert --close"; then
  should_close_signal=1
fi
if echo "$handshake_body" | grep -qi "close" && echo "$handshake_body" | grep -qi "signal"; then
  should_close_signal=1
fi
if echo "$handshake_body" | grep -qi "status again"; then
  should_status_after=1
fi
if echo "$handshake_body" | grep -qi "re-run status"; then
  should_status_after=1
fi
if echo "$handshake_body" | grep -qi "rerun planloop status"; then
  should_status_after=1
fi
if echo "$handshake_body" | grep -qi "rerun" && echo "$handshake_body" | grep -qi "status"; then
  should_status_after=1
fi

handle_signal() {
  echo "Opening CI blocker signal"
  python3 - <<PY > /dev/null
import os
from pathlib import Path
from planloop.home import SESSIONS_DIR
from planloop.core.session import load_session_state_from_disk, save_session_state
from planloop.core.signals import Signal, open_signal, close_signal
from planloop.core.state import SignalLevel, SignalType

home = Path(os.environ["PLANLOOP_HOME"])
session_dir = home / SESSIONS_DIR / os.environ["PLANLOOP_SESSION"]
state = load_session_state_from_disk(session_dir)
signal = Signal(
    id=os.environ["PLANLOOP_LAB_SIGNAL_ID"],
    kind="lab",
    title="CI blocked",
    message="Simulated blocker",
    level=SignalLevel.BLOCKER,
    type=SignalType.CI,
)
try:
    open_signal(state, signal=signal)
except ValueError:
    state.signals[:] = [s for s in state.signals if s.id != signal.id]
    open_signal(state, signal=signal)
save_session_state(session_dir, state, message="Lab signal open")
PY
  log_entry "signal-open" "id=$signal_id"
}

close_signal() {
  echo "Closing CI blocker signal"
  python3 - <<PY > /dev/null
import os
from pathlib import Path
from planloop.home import SESSIONS_DIR
from planloop.core.session import load_session_state_from_disk, save_session_state
from planloop.core.signals import close_signal

home = Path(os.environ["PLANLOOP_HOME"])
session_dir = home / SESSIONS_DIR / os.environ["PLANLOOP_SESSION"]
state = load_session_state_from_disk(session_dir)
close_signal(state, os.environ["PLANLOOP_LAB_SIGNAL_ID"])
save_session_state(session_dir, state, message="Lab signal closed")
PY
  log_entry "signal-close" "id=$signal_id"
}

log_entry "run-start" "session=$session workspace=$workspace"

if [ "$should_run_status" -eq 0 ]; then
  echo "1. Status (pre-update)"
  python3 -m planloop.cli status --session "$session" >/tmp/status-before.json
  reason=$(read_now_reason /tmp/status-before.json)
  log_entry "status-before" "reason=$reason"
else
  log_entry "status-before" "skipped"
fi

if [ "$inject_signal" -eq 1 ]; then
  handle_signal
else
  log_entry "signal-open" "none"
fi

echo "2. Update tasks via structured payload"
cat <<EOF >/tmp/update.json
{
  "session": "$session",
  "tasks": [
    { "id": 1, "status": "IN_PROGRESS" },
    { "id": 2, "status": "WAITING" }
  ],
  "context_notes": [
    "Lab-driven update: ${should_run_status:+status-first enforced, }applied simple patch."
  ],
  "next_steps": [
    "Finish the hello command code",
    "Keep tests green before advancing task 2"
  ],
  "final_summary": "Updated task 1 to IN_PROGRESS after confirming status."
}
EOF

python3 -m planloop.cli update --session "$session" --file /tmp/update.json
log_entry "update" "status=completed"

if [ "$inject_signal" -eq 1 ]; then
  if [ "$ignore_signal" -eq 0 ]; then
    close_signal
  else
    log_entry "signal-close-skipped" "id=$signal_id"
  fi
fi

echo "3. Status (post-update)"
if [ "$should_status_after" -eq 1 ] ; then
  python3 -m planloop.cli status --session "$session" >/tmp/status-after.json
  reason=$(read_now_reason /tmp/status-after.json)
  log_entry "status-after" "reason=$reason"
else
  log_entry "status-after" "skipped"
fi

echo "Mock agent completed"
log_entry "run-end" "status=done"
