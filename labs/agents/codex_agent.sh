#!/usr/bin/env bash
set -euo pipefail
prompt=${PLANLOOP_LAB_AGENT_PROMPT:-"Close the CI blocker, rerun status, and update tasks."}

codex exec "$prompt" --sandbox workspace-write
