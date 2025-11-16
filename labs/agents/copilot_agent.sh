#!/usr/bin/env bash
set -euo pipefail
prompt=${PLANLOOP_LAB_AGENT_PROMPT:-"Close the CI blocker, rerun status, and resume the plan."}

copilot -p "$prompt" --allow-all-paths --allow-all-tools --model gpt-5 --no-color --deny-tool "shell(gh:*)"
