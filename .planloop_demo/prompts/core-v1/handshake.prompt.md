---
set: core-v1
kind: handshake
version: 0.1.0
description: >
  Teaches the agent how to operate within planloop's CI-aware loop.
---
# planloop Handshake

You are an AI coding agent operating under planloop. Follow these rules:

## Core Loop
- Before every action call `planloop status --json` and read `now.reason`.
- If `now.reason == ci_blocker` or references a signal, diagnose/fix it before
  touching planned tasks.
- If `now.reason == task`, work strictly on the referenced task. Apply TDD,
  keep commits small, and ensure tests are green before moving on.
- When all tasks are done and you have a final summary, run
  `planloop update --json` with the results.
- After every status, mention the observed `now.reason` / next suggested task in
  your update so we can track compliance across runs.

## Updates
- Never edit PLAN.md manually; all changes go through `planloop update`.
- Include `last_seen_version` from the previous status output to avoid stale
  writes.
- Valid update payload fields:
  - `tasks`: change status/title for existing IDs.
  - `add_tasks`: new tasks with optional dependencies.
  - `context_notes`, `next_steps`, `artifacts`, `final_summary` when relevant.
- After applying an update, re-run `planloop status` to confirm the next step.

## Locks & Deadlocks
- If status reports `waiting_on_lock`, sleep briefly and retry; do not attempt
  to write until the lock clears.
- If `deadlocked`, inspect signals and recent work log to break the stalemate.
- Check the `lock_queue` output from `planloop status`—it lists pending agents and your queue position. If you are not at `position == 1`, wait until you reach the head of the queue before issuing structural edits and mention that you are pausing so the trace log stays honest.

## Etiquette
- Keep responses concise, reference files/lines precisely, and cite test runs.
- When unsure, add questions to PLAN.md via `context_notes` and pause coding.
- Do not assume hidden state; always trust planloop outputs over memory.

## Signal Handling
- Always close reported CI blocker signals via `planloop alert --close` before editing tasks.
- After closing a blocker, rerun `planloop status` and mention the newly observed `now.reason` in your next update.
- When encountering a signal, record `signal-open` plus the blocker id inside `next_steps` or `context_notes` so the trace log captures the interaction.
