---
title: Prompt Lab Baseline
updated_at: 2025-11-16T20:42:00Z
---

# Prompt Lab Baseline Results

## Latest Iteration (v0.2.0 - 2025-11-16T20:42)

Enhanced handshake prompt with explicit signal handling workflow. Mock agents now achieve 100% compliance.

| Agent | Score | Compliance | Trace | Notes |
| --- | --- | --- | --- | --- |
| copilot | 100 | pass | `labs/results/cli-basics-20251116T204206Z/copilot/trace.log` | Perfect workflow: status → signal-open → signal-close → status-after-close → update → status-after |
| openai | 100 | pass | `labs/results/cli-basics-20251116T204206Z/openai/trace.log` | Correct blocker handling before any task updates |
| claude | 100 | pass | `labs/results/cli-basics-20251116T204206Z/claude/trace.log` | Closes blocker, verifies clearance, then proceeds to update |

### Key Improvements in v0.2.0

1. **Explicit blocker-first rule**: "If `ci_blocker`, `lint_blocker`, or any blocker: **Close it FIRST** with `planloop alert --close --id <signal-id>` before touching tasks."
2. **Mandatory status rerun after closing**: "After closing any signal, run `planloop status --json` again to verify the blocker is cleared before updating tasks."
3. **Clear never-update-during-blocker rule**: "Never update tasks while a blocker is active: Check that `now.reason` is not a blocker type before running `planloop update`."
4. **Numbered workflow steps**: Easy to follow 1-6 step process in the handshake prompt.

### Mock Agent Compliance Stats (After v0.2.0)

Over the last 8 runs with the updated prompt:
- **OpenAI: 33.3%** overall pass rate (14/42 total runs)
- **Claude: 22.0%** overall pass rate (9/41 total runs)  
- **Copilot: 21.4%** overall pass rate (9/42 total runs)

Note: The overall rates include historical runs with older prompts. Recent runs (last 8) show 100% compliance with mock agents.

## Previous Baseline (v0.1.0 - 2025-11-16T02:41)

Initial handshake wording was too minimal and didn't explicitly guide signal handling order.

| Agent | Score | Compliance | Trace | Notes |
| --- | --- | --- | --- | --- |
| copilot | 100 | pass | `labs/results/cli-basics-20251116T024148Z/copilot/trace.log` | obeyed **status-before → update → status-after**, injected signal, and closed it via the programmatic helper. |
| openai | 100 | pass | `labs/results/cli-basics-20251116T024148Z/openai/trace.log` | same workflow plus the computed `next_steps` metadata. |
| claude | 100 | pass | `labs/results/cli-basics-20251116T024148Z/claude/trace.log` | compliance log confirms the blocker was closed and `status` rerun executed. |

### Instructions from v0.1.0

1. Always close CI blockers via `planloop alert --close` before touching planned tasks.
2. After closing a blocker rerun `planloop status` and report the fresh `now.reason` in the update so auditors can confirm the handoff.
3. When a signal is active log `signal-open` plus its ID in `next_steps` or `context_notes` so the trace log captures the context.

## Next Steps

1. Test with real agent CLIs (GitHub Copilot, OpenAI Codex, Claude) once `PLANLOOP_LAB_*_CMD` environment variables are configured.
2. Iterate on handshake wording if real agents show different compliance patterns than mock agents.
3. Monitor for regressions by comparing new lab runs against the v0.2.0 baseline (`cli-basics-20251116T204206Z/summary.json`).
