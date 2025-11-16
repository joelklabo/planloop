#!/usr/bin/env bash
set -euo pipefail
prompt=${PLANLOOP_LAB_AGENT_PROMPT:-"Close the CI blocker, rerun status, and then update the plan."}

claude -p "$prompt" --print --allowedTools "Bash"
