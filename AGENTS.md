# planloop – Agent Guide

Welcome! This repository is currently empty except for planning artifacts. Our
source of truth for implementation work lives in `docs/plan.md`, which breaks
the v1.5 specification into milestones populated with commit-sized tasks. Read
that document before you start coding—every task lists scope, deliverables,
acceptance criteria, and dependencies.

## Mission
Build `planloop`, a local tool that keeps AI coding agents in a strict,
CI-aware loop driven by `state.json` + `PLAN.md` pairs stored under
`PLANLOOP_HOME`. The end goal is a deterministic CLI/TUI/Web experience where
agents always:
1. Ask `planloop status` to know what to do next.
2. Clear blocking signals (CI, lint, custom scripts) before working on tasks.
3. Update the plan exclusively through structured payloads (`planloop update`).
4. Respect locks and versioning so no work happens on stale state.

## Ground Rules
- Treat `docs/plan.md` as the queue. Update task status there before/after each
  commit so humans and agents stay aligned.
- Keep changes atomic. If a task feels too big for one commit, split it inside
  the plan before touching code.
- Tests accompany every behavior that could silently regress (state validation,
  locking, CLI commands, rendering, etc.).
- PLANLOOP_HOME must never leak secrets—assume sessions live outside the repo.

## Getting Started
1. **Read the plan:** `docs/plan.md` → Milestone 0 (Tasks A1–A4) is the current
   focus since the repo has no code yet.
2. **Follow task ordering:** Later milestones depend on the foundations, so
   don't skip ahead without updating the plan.
3. **Document progress:** When you finish a task, mark it as done in the plan
   and note any context or follow-ups.

## Key Directories (as planned)
- `src/planloop/`: core package (CLI, state machine, prompts loader, etc.).
- `tests/`: pytest suite (unit + integration + self-test harness).
- `docs/`: planning artifacts (this file + plan) and future design notes.

## High-Level Roadmap
- **Milestone 0:** bootstrap repo + packaging + placeholder CLI.
- **Milestone 1:** PLANLOOP_HOME discovery and initialization scaffolding.
- **Milestone 2:** Session state models and PLAN.md renderer.
- **Milestones 3–13:** Sessions lifecycle, state machine, lock handling, CLI
  commands, prompts, TUI/Web dashboards, history/snapshots, self-test harness,
  logging, and safe-mode options.

Each milestone in `docs/plan.md` specifies the required functionality, so treat
this file as high-level orientation and keep the plan updated for actionable
work.
