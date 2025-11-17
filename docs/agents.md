# planloop – Agent Guide

v1.5 is complete! All core features are implemented and tested. Use this guide plus
`docs/plan.md` for current work. Focus is now on agent testing and optimization.

## Project Organization

### Documentation Structure
All documentation lives in `docs/`:
- **`docs/agents.md`** (this file) - Agent workflow contract, symlinked to:
  - `AGENTS.md` (root)
  - `CLAUDE.md` (root)  
  - `.github/copilot-instructions.md` (GitHub Copilot)
- **`docs/plan.md`** - Development plan (active work, backlog, what's built)
- **`docs/architecture.md`** - System design reference
- **`docs/lab-testing.md`** - Testing infrastructure guide
- **`docs/agent-performance.md`** - Auto-generated test metrics
- **`docs/archive/`** - Historical documentation (v1.5 task list)

**Naming Convention**: All markdown files use `lowercase-with-hyphens.md`

### Temporary Files
**CRITICAL**: Use `tmp/` folder at project root for ALL temporary files, logs, debug output, etc.
- ✅ **DO**: Write to `tmp/debug.log`, `tmp/analysis.json`, etc.
- ❌ **DON'T**: Create temp files in project root, use system `/tmp`, or scatter files elsewhere
- This folder is gitignored and safe for any temporary work

## Source of Truth
- **`docs/plan.md`** - Current work and backlog
- **`docs/agents.md`** (this file) - Workflow rules and command reference
- Re-run `planloop guide --target agents-md --apply` when prompts/workflow change

## Workflow contract
1. **Always** call `planloop status --json` to decide the next action. Respect
   `now.reason`:
   - `ci_blocker` → fix the signal before touching tasks.
   - `task` → implement the referenced task using TDD.
   - `waiting_on_lock` → sleep and retry `status`.
2. **Don’t wait for optional direction** — once a task is done (or a signal is cleared), pick the next `Status: TODO` item from `docs/plan.md`, mark it `IN_PROGRESS`, and keep going. Treat the plan as your instruction set; do not ask “what should I do next?” or seek confirmation before acting, even while processing blockers—just handle the signal, rerun status, and move to the next step autonomously unless a human explicitly interrupts you.
3. **Practice TDD**: write/update tests, watch them fail, implement, rerun
   tests, then refactor.
4. **Commit often**: each task should fit in a single commit.
   If work balloons, split the task in the plan before writing code.
5. **Never** commit failing tests. Local WIP stays local.
6. **Update the plan**: mark tasks `IN_PROGRESS` when you start, add context
   while working, and record completion status when finished.

## Key commands
- `planloop status --json` → always the first step; surfaces tasks, signals,
  lock info, and agent instructions.
- `planloop update --file payload.json` → edit tasks/context via validated JSON
  payloads instead of editing PLAN.md directly.
- Safe modes:
  - `planloop update --dry-run` → preview state changes without writing.
  - `planloop update --no-plan-edit` → only change task statuses.
  - `planloop update --strict` → reject payloads with unknown fields.
  - Configure defaults in `~/.planloop/config.yml` under `safe_modes.update`
    (e.g., enforce `no_plan_edit: true` for all agents).
- `planloop alert ...` → open/close CI, lint, bench, or system signals that
  gate the loop.
- `planloop sessions list/info`, `planloop search`, `planloop templates`,
  `planloop reuse` → discover prior work or bootstrap new sessions from
  templates.
- `planloop guide --apply` → refresh this file with the latest contract.
- `planloop view` / `planloop web` → read-only dashboards (require `textual`
  and `fastapi`+`uvicorn` respectively). Both commands detect missing deps and
  tell you what to install.
- `planloop snapshot` / `planloop restore <sha>` → manage per-session history
  (requires git and `history.enabled: true` in `~/.planloop/config.yml`).
- `planloop selftest --json` → run the fake-agent harness. It creates a
  temporary PLANLOOP_HOME, executes clean/CI/dependency scenarios, and reports
  whether the loop still behaves end-to-end.
- `python labs/run_lab.py --scenario cli-basics --agents copilot,openai,claude` →
  execute the automated prompt lab for all agents once their adapter commands are
  wired via `PLANLOOP_LAB_*_CMD`.

## History + snapshots quickstart
1. Run `planloop status` once to create `PLANLOOP_HOME` (defaults to
   `~/.planloop`).
2. Edit `config.yml` there, set `history.enabled: true`.
3. Work through tasks; every call to `save_session_state` makes a git commit in
   each session directory, using the generated `.gitignore` to ignore logs and
   artifacts.
4. Take snapshots before risky work: `planloop snapshot --session <session>`.
5. Roll back with `planloop restore <sha> --session <session>` – this resets the
   session repo, refreshes the registry, and revalidates the plan. Rerun tests
   immediately after restoring.

## Getting started checklist
1. Create/activate a Python 3.11+ virtualenv and `pip install -e .[dev]`.
2. Run `planloop guide --apply` if the workflow changed.
3. Pick the next `Status: TODO` task from `docs/plans/plan.md`, mark it
   `IN_PROGRESS`, follow the workflow contract, and keep looping until the plan
   is empty.
