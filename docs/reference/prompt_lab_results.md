---
title: Prompt Lab Baseline
updated_at: 2025-11-16
---

# Prompt Lab Baseline Results

After caring for the compliance harness we captured a reliable baseline run with the current handshake wording plus the three signal-focused instructions we iterated via `planloop/labs/optimize_prompt.sh`.

| Agent | Score | Compliance | Trace | Notes |
| --- | --- | --- | --- | --- |
| copilot | 100 | pass | `labs/results/cli-basics-20251116T024148Z/copilot/trace.log` | obeyed **status-before → update → status-after**, injected signal, and closed it via the programmatic helper. |
| openai | 100 | pass | `labs/results/cli-basics-20251116T024148Z/openai/trace.log` | same workflow plus the computed `next_steps` metadata. |
| claude | 100 | pass | `labs/results/cli-basics-20251116T024148Z/claude/trace.log` | compliance log confirms the blocker was closed and `status` rerun executed. |

## Instructions that worked

1. Always close CI blockers via `planloop alert --close` before touching planned tasks.
2. After closing a blocker rerun `planloop status` and report the fresh `now.reason` in the update so auditors can confirm the handoff.
3. When a signal is active log `signal-open` plus its ID in `next_steps` or `context_notes` so the trace log captures the context.

Keep these lines as the guaranteed “best version” of the handshake prompt. When we continue iterating, compare new wording + lab summaries against this benchmark (`cli-basics-20251116T024148Z/summary.json`) so regressions are obvious.
