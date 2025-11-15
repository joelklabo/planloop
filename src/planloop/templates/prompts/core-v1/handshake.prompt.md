---
set: core-v1
kind: handshake
version: 0.1.0
description: >
  Teaches the agent how to operate within planloop's CI-aware loop.
---
# planloop Handshake (Placeholder)

- Always run `planloop status --json` to decide what to do next.
- Respect `now.reason`: blockers beat tasks, deadlocks require escalation.
- Use `planloop update --json` with strict payloads; never edit PLAN.md directly.
