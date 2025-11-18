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
- **`docs/reference/agent-prompting-guide.md`** - Agent-specific prompt optimization
- **`docs/reference/agent-troubleshooting.md`** - Common issues and solutions
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
## Workflow contract
1. **Always** call `planloop status --json` to decide the next action. Respect
   `now.reason`:
   - `ci_blocker` → fix the signal before touching tasks.
   - `task` → implement the referenced task using TDD.
   - `waiting_on_lock` → sleep and retry `status`.
   - `completed` + empty plan → run `planloop suggest` to discover new work.
2. **Don't wait for optional direction** — once a task is done (or a signal is cleared), pick the next `Status: TODO` item from `docs/plan.md`, mark it `IN_PROGRESS`, and keep going. Treat the plan as your instruction set; do not ask "what should I do next?" or seek confirmation before acting, even while processing blockers—just handle the signal, rerun status, and move to the next step autonomously unless a human explicitly interrupts you.
3. **Discover work proactively** — when the plan is empty or you're asked "what's
   next?", run `planloop suggest` to analyze the codebase for gaps, technical
   debt, and improvements. It generates context-rich tasks ready for implementation.
4. **Practice TDD**: write/update tests, watch them fail, implement, rerun
   tests, then refactor.
5. **Commit often**: each task should fit in a single commit.
   If work balloons, split the task in the plan before writing code.
6. **Never** commit failing tests. Local WIP stays local.
7. **Update the plan**: mark tasks `IN_PROGRESS` when you start, add context
   while working, and record completion status when finished.

## Key commands
- `planloop status --json` → always the first step; surfaces tasks, signals,
  lock info, and agent instructions.
- `planloop suggest` → **AI-powered task discovery**. Analyzes the codebase and
  current plan to suggest new tasks. Use this when:
  - The plan is empty or all tasks are complete
  - You need context-aware work suggestions
  - User asks "what should I work on next?"
  - You want to find technical debt, missing tests, or improvement opportunities
  
  **Options**:
  - `--dry-run` → Preview suggestions without adding to plan
  - `--auto-approve` → Skip interactive approval, add all suggestions
  - `--limit N` → Limit to N suggestions (default: 5)
  - `--depth shallow|medium|deep` → Analysis depth (default: medium)
  - `--focus PATH` → Focus analysis on specific directory
  
  **Example workflow**:
  ```bash
  # Check status - no tasks left
  planloop status --json
  # Output: "now": {"reason": "completed"}
  
  # Discover new work
  planloop suggest
  # Reviews 5 suggestions interactively, add 3 of them
  
  # Continue working
  planloop status --json
  # Output: "now": {"reason": "task", "task_id": 15}
  ```
  
  **Configuration**: Set defaults in `~/.planloop/config.yml`:
  ```yaml
  suggest:
    llm:
      provider: openai  # or anthropic, ollama
      model: gpt-4o-mini
      api_key_env: OPENAI_API_KEY
    context:
      depth: medium
      include_git_history: true
    suggestions:
      max_count: 5
  ```
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

## Development Environment Setup

**CRITICAL**: This project requires Python 3.11+ and uses `uv` for fast, reproducible environment management.

### First-Time Setup
```bash
# Automated setup (installs uv if needed, creates venv, installs all deps)
./setup-dev.sh

# Activate environment
source .venv/bin/activate

# Verify everything works
./verify-env.sh
```

### Every Time You Work
**ALWAYS activate the virtual environment before running any Python commands:**
```bash
source .venv/bin/activate
```

Then you can run:
```bash
python --version      # Should be 3.11.x
pytest tests/ -v      # Run tests
planloop status       # Use planloop commands
make test             # Run tests via Make
```

### If Environment Is Broken
```bash
# Reset everything
./setup-dev.sh

# Or verify what's wrong
./verify-env.sh
```

### Common Issues

**Problem**: `python: command not found` or wrong Python version  
**Solution**: Activate the venv first: `source .venv/bin/activate`

**Problem**: Import errors or `ModuleNotFoundError`  
**Solution**: Reinstall dependencies: `uv pip install -e ".[dev]"`

**Problem**: Tests fail with `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`  
**Solution**: You're using Python 3.9. This project requires 3.11+. Run `./setup-dev.sh`

### Available Make Commands
```bash
make help      # Show all available commands
make setup     # Run ./setup-dev.sh
make test      # Run all tests
make lint      # Run ruff + mypy
make format    # Auto-format code
make clean     # Remove build artifacts
```

### Quick Reference
- **Setup script**: `./setup-dev.sh` - One command to set up everything
- **Verification**: `./verify-env.sh` - Check if environment is healthy
- **Documentation**: `docs/development-setup.md` - Detailed setup guide
- **Python version**: `.python-version` - Specifies Python 3.11 requirement

## Getting started checklist
1. **Set up environment**: Run `./setup-dev.sh` and activate with `source .venv/bin/activate`
2. **Verify setup**: Run `./verify-env.sh` to ensure everything works
3. **Start working**: Pick the next `Status: TODO` task from `docs/plan.md`, mark it
   `IN_PROGRESS`, follow the workflow contract, and keep looping until the plan
   is empty.
