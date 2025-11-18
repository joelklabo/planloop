# planloop

[![CI](https://github.com/joelklabo/planloop/actions/workflows/ci.yml/badge.svg)](https://github.com/joelklabo/planloop/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/joelklabo/planloop/branch/main/graph/badge.svg)](https://codecov.io/gh/joelklabo/planloop)

Agent-first local planning loop that keeps AI coders synced with CI signals
using structured markdown plans. `docs/plans/plan.md` is the living backlog; update it
before and after every commit so humans and agents stay aligned.

## Agent Performance

Real agent testing with automated compliance tracking:

![claude:sonnet](https://img.shields.io/badge/claude_sonnet-26.1%25-orange) **21.8/100**
![copilot:gpt-5](https://img.shields.io/badge/copilot_gpt--5-26.5%25-orange) **21.7/100**

See [Agent Performance Data](docs/agent-performance.md) for detailed metrics and improvement tracking.

## Requirements
- Python 3.11+
- macOS or Linux shell (Windows support later)

## Quick Setup

We use [uv](https://github.com/astral-sh/uv) for fast, reproducible Python environment management.

```bash
# Automated setup (installs uv if needed, creates venv, installs deps)
./setup-dev.sh

# Activate environment
source .venv/bin/activate

# Run tests
make test
```

### Manual setup (if you prefer)
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv with exact Python version
uv venv --python 3.11

# Install dependencies
uv pip install -e ".[dev]"

# Activate and verify
source .venv/bin/activate
python --version  # Should be 3.11.x
```

### Available Make targets
```bash
make help     # Show all available commands
make setup    # Run setup-dev.sh
make test     # Run all tests
make lint     # Run ruff + mypy
make format   # Auto-format code
make clean    # Remove build artifacts
```

## Workflow expectations
- Practice TDD whenever practical: write or update tests, watch them fail, make
  them pass, then refactor.
- Commit early/often. When you pick up a task from `docs/plans/plan.md`, set its
  status to `IN_PROGRESS`, implement the change, run tests, commit, push,
  update the plan with the commit SHA, then grab the next task.
- Never commit failing tests. If work is incomplete, keep it local and leave
  the plan entry as `TODO`.

## Core CLI commands
Most commands accept `--json` for agent consumption.

| Command | Purpose |
| --- | --- |
| `planloop status [--session <id>]` | Inspect the current session, lock status, tasks, and signals. |
| `planloop suggest [options]` | **NEW** AI-powered codebase analysis to discover tasks automatically. |
| `planloop update --file payload.json` | Apply structured plan/task updates. |
| `planloop alert --session <id> ...` | Open/close CI, lint, or custom blocker signals. |
| `planloop describe --json` | Emit JSON Schemas for state and update payloads. |
| `planloop sessions list/info` | Browse the session registry. |
| `planloop search / templates / reuse` | Discover or reuse prior sessions. |
| `planloop view` | Launch the Textual TUI (requires `textual`). |
| `planloop web` | Serve a minimal FastAPI dashboard (requires `fastapi` + `uvicorn`). |
| `planloop guide --target agents-md --apply` | Inject the agent contract into `docs/agents.md`. |
| `planloop update --dry-run/--no-plan-edit/--strict` | Safe modes for previewing or constraining updates. |
| `planloop snapshot` / `planloop restore <sha>` | Manage session history snapshots (see below). |

`planloop selftest` runs the built-in fake agent harness. It spins up a
temporary PLANLOOP_HOME, executes several scripted scenarios (clean run, CI
blocker, dependency chain), and reports JSON results so you know the loop still
works end-to-end.

## AI-Powered Task Discovery

**NEW in v1.6**: `planloop suggest` analyzes your codebase and suggests tasks automatically.

The AI examines:
- Project structure and code patterns
- TODO/FIXME comments
- Recent git changes
- Missing tests and documentation
- Technical debt opportunities

### Basic Usage

```bash
# Analyze codebase and get suggestions
planloop suggest

# Preview suggestions without adding to plan
planloop suggest --dry-run

# Focus on specific area
planloop suggest --focus src/auth

# Deeper analysis (slower, more thorough)
planloop suggest --depth deep

# Auto-approve all suggestions
planloop suggest --auto-approve

# Limit number of suggestions
planloop suggest --limit 3
```

### Configuration

Create `~/.planloop/config.yml` to customize:

```yaml
suggest:
  llm:
    provider: openai  # or anthropic, ollama
    model: gpt-4o-mini
    api_key_env: OPENAI_API_KEY
  context:
    depth: medium  # shallow, medium, deep
    include_git_history: true
  suggestions:
    max_count: 5
```

API keys can be set via environment variables (e.g., `OPENAI_API_KEY`) or in the config.

### Agent Workflow

When agents run `planloop status` and see no tasks, they'll be prompted to use `planloop suggest`:

```json
{
  "now": {"reason": "idle"},
  "agent_instructions": "No tasks defined. Run 'planloop suggest' to discover work..."
}
```

This enables fully autonomous task discovery when agents run out of work.

## Session history, snapshots, and restore
`planloop` can keep a per-session git repo so you can checkpoint plan state
independently of your project repo.

1. Run any `planloop` command once to create `~/.planloop` (or point
   `PLANLOOP_HOME` elsewhere for testing).
2. Open `~/.planloop/config.yml` and set:

   ```yaml
   history:
     enabled: true
   ```

   (Use `planloop.config.reset_config_cache()` in tests to reload.)
3. Create or open a session. Every call to `save_session_state` will now commit
   `state.json`, `PLAN.md`, and the generated `.gitignore` inside the session
   directory.
4. To checkpoint progress, run:

   ```bash
   planloop snapshot --session <session-id> --note "Before risky refactor"
   ```

   The command prints the snapshot SHA.
5. To roll back, run:

   ```bash
   planloop restore <sha> --session <session-id>
   ```

   This performs `git reset --hard`, reloads `state.json`, updates the session
   registry, and validates the restored plan. Always rerun tests after a restore
   before committing new work.

Snapshots require `git` on your PATH. When history is disabled, the commands
exit with a descriptive error.

## Optional UI dependencies
- `pip install textual` enables `planloop view`.
- `pip install 'fastapi[standard]' uvicorn` enables `planloop web`.

Both commands detect missing dependencies and print clear instructions.

## Lock queue visibility
`planloop status` now surfaces a `lock_queue` section that lists the agents currently waiting on the session lock and the caller’s position in that queue. Agents should only attempt structural edits (updates/alerts) when their `position` is `1`; if you are waiting, mention the queue status in your plan update so humans and auditors can follow along.

## 📊 Agent Performance Data

**Total Test Runs:** 35 | **Latest:** `cli-basics-20251116T085040Z-6fc8`

### Compliance Rates
![claude](https://img.shields.io/badge/claude-6.1%25-red) ![copilot](https://img.shields.io/badge/copilot-5.9%25-red) ![openai](https://img.shields.io/badge/openai-20.6%25-red)

| Agent | Runs | Passes | Fails | Pass Rate | Top Errors |
|-------|------|--------|-------|-----------|------------|
| claude | 33 | 2 | 31 | 6.1% | missing status-after (18), missing update (14) |
| copilot | 34 | 2 | 32 | 5.9% | missing status-after (17), missing update (16) |
| openai | 34 | 7 | 27 | 20.6% | trace log missing (14), missing status-after (13) |

*Data from automated lab runs testing workflow compliance. See [docs/agent-performance.md](docs/agent-performance.md) for details. Stats auto-update via GitHub Actions.*


## Prompt lab leaderboard

We run an automated **prompt lab** that seeds a session, injects a CI blocker signal, and drives every CLI agent (Copilot CLI, OpenAI runner, Claude adapter) through the workflow while collecting a `trace.log`. Each run now computes a **compliance score (0‑100)** that rewards the `status-before → update → status-after` path, closing blockers before writing tasks, and avoiding edits while a signal is open. The latest scoreboard and trace references are in [`docs/prompt_lab_results.md`](docs/prompt_lab_results.md).  

To add a new CLI/model combination, point its adapter to `planloop/labs/agents/mock_agent.sh`, rerun `planloop/labs/optimize_prompt.sh`, and publish the resulting JSON in `labs/results/cli-basics-*`. The README, docs, and scoring logic will automatically treat every run as part of the leaderboard.

## Logging
`planloop` writes per-session logs to `sessions/<id>/logs/planloop.log`. You can
adjust the default level by editing `~/.planloop/config.yml`:

```yaml
logging:
  level: DEBUG
```

Key commands (status/update/alert/snapshot/restore/selftest) append entries so
you can inspect what happened without rerunning the CLI.

## Update safe modes
- `--dry-run`: parse + validate payloads, show a diff summary (added/updated
  tasks, context/final summary changes), and exit without writing anything.
- `--no-plan-edit`: reject structural edits (`add_tasks`, `update_tasks`,
  context/next steps, artifacts) so you can only change task statuses.
- `--strict`: reject payloads that contain any unknown top-level keys (useful
  when integrating with agents that might emit extra metadata).

Project defaults live in `~/.planloop/config.yml` under `safe_modes.update`.
For example:

```yaml
safe_modes:
  update:
    dry_run: true
    no_plan_edit: true
    strict: false
```

These defaults apply automatically unless you pass the explicit override flag
(`--no-dry-run`, `--allow-plan-edit`, `--allow-extra-fields`). `planloop status`
surfaces the currently enforced defaults so agents can adapt.

## Prompt Lab (Copilot/OpenAI/Claude)
Use `labs/run_lab.py` to exercise real agents against deterministic scenarios.
Each adapter shells out to a user-provided command so you can plug in Copilot
CLI, OpenAI/Codex, or Claude.

1. Create helper scripts/commands that drive each agent. Export their paths:

   ```bash
   export PLANLOOP_LAB_COPILOT_CMD="copilot-runner.sh"
   export PLANLOOP_LAB_OPENAI_CMD="python labs/adapters/openai_runner.py"
   export PLANLOOP_LAB_CLAUDE_CMD="claude --config labs/claude.yaml"
   ```
2. Run the lab:

   ```bash
   PYTHONPATH=src python labs/run_lab.py --scenario cli-basics --agents copilot,openai,claude
   ```

   The orchestrator creates a temp PLANLOOP_HOME, seeds the scenario, and runs
   each enabled agent. Results (stdout/stderr + summary JSON) land under
   `labs/results/<scenario>-<timestamp>/`.

The environment passed to each agent includes:

- `PLANLOOP_HOME` – temp home for the scenario
- `PLANLOOP_SESSION` – session ID to target
- `PLANLOOP_LAB_SCENARIO` – scenario name (e.g., `cli-basics`)
- `PLANLOOP_LAB_WORKSPACE` – repository root to run commands in
- `PLANLOOP_LAB_RESULTS` – directory for any extra artifacts

Add your own scenarios (see `labs/scenarios/`) and expand the adapters to call
your preferred agent tooling.

## Contributing
1. Read `docs/plan.md` for the current milestone. Mark tasks `IN_PROGRESS`
   before editing code and record commit SHAs when closing them.
2. Follow the workflow expectations above (TDD, frequent commits, no failing
   tests on main).
3. Keep changes scoped to a single task/commit. If a task proves too large,
   split it in the plan before coding.
4. Update `docs/agents.md` via `planloop guide` whenever you change the workflow so
   future agents inherit the latest contract.
