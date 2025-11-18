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
1. **Always** call `planloop status --json` to decide the next action. The response
   includes:
   - **`next_action`**: Explicit guidance on what to do next
     - `action: "continue"` + `task_id` → Start the next task immediately.
     - `action: "fix_blocker"` + `signal_id` → Fix the signal before tasks.
     - `action: "discover"` → Run `planloop suggest` to find new work.
     - `action: "wait"` → Session locked, retry status after a delay.
   
   - **`transition_detected`**: Boolean indicating a task just completed
   - **`completed_task_id`**: ID of the just-completed task (when transition detected)
   
   Also respect `now.reason` for context:
   - `ci_blocker` → fix the signal before touching tasks.
   - `task` → implement the referenced task using TDD.
   - `waiting_on_lock` → sleep and retry `status`.
   - `completed` → all tasks done, suggest or add final_summary.
   
2. **Autonomous continuation is required** — After completing any task or fixing a
   signal, immediately call `planloop status --json` again and follow the
   `next_action`. **Never** stop to ask "what should I do next?" or wait for
   confirmation. The workflow is:
   - Complete task → mark DONE → `planloop status` → read `next_action` → continue
   - Fix signal → close alert → `planloop status` → read `next_action` → continue
   - This loop continues until `action: "discover"` or human interruption.
   
3. **Discover work proactively** — when `next_action.action == "discover"`, run
   `planloop suggest` to analyze the codebase for gaps, technical debt, and
   improvements. It generates context-rich tasks ready for implementation.
   
4. **Practice TDD religiously** — This is NON-NEGOTIABLE:
   
   **The TDD Cycle (for every task):**
   ```
   [ ] 1. Write test first (or update existing test)
   [ ] 2. Run tests → watch the new test FAIL
   [ ] 3. Implement minimal code to make it pass
   [ ] 4. Run tests → verify ALL tests PASS
   [ ] 5. Refactor if needed (keeping tests green)
   [ ] 6. Commit with descriptive message
   ```
   
   **Never skip this cycle**. Tests are the contract. If you're tempted to skip
   tests, split the task into smaller pieces in the plan first. No test = no commit.
   
5. **Commit often**: each task should fit in a single commit.
   If work balloons, split the task in the plan before writing code.
   
6. **Never** commit failing tests. Local WIP stays local.

7. **Update the plan**: mark tasks `IN_PROGRESS` when you start, add context
   while working, and record completion status when finished.

8. **Provide feedback on issues** — When you encounter problems, confusion, bugs,
   or UX friction, immediately report it using `planloop feedback`:
   ```bash
   planloop feedback --message "Issue description" --rating 3
   ```
   This helps improve planloop for all agents. Report feedback whenever:
   - Commands behave unexpectedly or produce confusing output
   - Documentation is unclear or incorrect
   - Workflow requires unnecessary manual steps
   - Tests fail in surprising ways
   - You discover bugs or edge cases
   - The TDD cycle is interrupted by tooling issues
   
   When all tasks complete, `planloop status` will prompt you to reflect on the
   session with a feedback request. Always complete this reflection.

## Autonomous Loop Example
**This is how agents should work continuously without stopping:**

```bash
# 1. Check what to do
planloop status --json
# Response: "next_action": {"action": "continue", "task_id": "P1.1", ...}

# 2. Work on P1.1 using TDD (THE CHECKLIST!)
# [ ] Write test in tests/test_feature.py
# [ ] Run pytest tests/test_feature.py → FAIL (red)
# [ ] Implement in src/feature.py
# [ ] Run pytest tests/test_feature.py → PASS (green)
# [ ] Refactor if needed (keep green)
# [ ] Commit: "feat: Add feature (P1.1)"

# 3. Mark complete and get next action
planloop update --file <payload-marking-P1.1-done>
planloop status --json
# Response: "next_action": {"action": "continue", "task_id": "P1.2", ...}

# 4. Immediately start P1.2 (NO stopping to ask!)
# Repeat TDD cycle for P1.2...

# 5. After P1.2 done, check again
planloop status --json
# Response: "next_action": {"action": "discover", ...}

# 6. Discover new work
planloop suggest

# 7. Continue with suggested tasks...
# The loop never stops until human intervenes or action is "wait"
```

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
- `planloop logs` → view agent interaction transcript (JSON Lines format)
  - `--limit N` → show last N entries (default: 50)
  - `--json` → output as JSON for parsing
  - Logs all commands, responses, and notes in `session_dir/logs/agent-transcript.jsonl`
  - Useful for debugging agent behavior and understanding decision flow
- `planloop feedback --message "..." [--rating 1-5]` → submit feedback about
  issues, bugs, or UX friction encountered during the session. **USE THIS
  PROACTIVELY** whenever you hit problems. Feedback is stored in
  `session_dir/feedback.json` and helps improve planloop for all agents.
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

## Bash Session Health Monitoring

**CRITICAL for CLI AI Agents**: Bash sessions suffer from PTY (pseudo-terminal) resource exhaustion after 30-50 commands, leading to `posix_spawnp failed` errors that brick the session.

### The Problem

Long-running agent sessions accumulate:
- **PTY file descriptors** → System limits exhausted (typically ~127 on macOS)
- **Process table entries** → Cannot spawn new commands
- **Memory leaks** → node-pty doesn't always clean up properly

**Symptoms**:
- Commands start hanging (20-30 commands in)
- Occasional "Connection reset" errors
- `posix_spawnp failed` → **session unusable, must restart**

### The Solution: Proactive Health Monitoring

Use `planloop monitor bash-health` to check session health **before** corruption occurs.

### When to Check Health

**Option 1: Periodic Checks** (Recommended for long sessions)
```bash
# Every 10-15 bash commands, check health:
planloop monitor bash-health --json

# If health_score < 60, consider rotating
# If health_score < 50, rotate immediately
```

**Option 2: Before Long-Running Work**
```bash
# Before running tests, builds, or complex commands:
planloop monitor bash-health

# If status is "degraded" or worse, rotate first
```

**Option 3: On Errors**
```bash
# If bash commands start failing mysteriously:
planloop monitor bash-health

# Check if PTY exhaustion is the cause
```

### Understanding the Health Score

**Score Range: 0-100**

- **80-100**: 🟢 **Healthy** - No action needed
  - Low command count (< 20)
  - Few PTYs (< 4)
  - Session is young
  
- **60-79**: 🟡 **Watch** - Monitor closely
  - Moderate command count (20-30)
  - PTY count increasing (4-6)
  - Consider rotating soon
  
- **40-59**: 🟠 **Degraded** - Rotation recommended
  - High command count (30-40)
  - Elevated PTYs (6-8)
  - **Rotate before reaching 50 commands**
  
- **20-39**: 🔴 **Critical** - Rotate immediately
  - Very high command count (> 50)
  - Many PTYs (> 10)
  - **Failure imminent**
  
- **0-19**: ⚫ **Failed** - Already corrupted
  - Session unusable
  - Create fresh bash session with new ID

### Command Usage

**Human-Readable Output:**
```bash
planloop monitor bash-health

# Output:
# 🟠 Bash Session Health: Degraded (Score: 50/100)
#
# Metrics:
#   Commands: 38
#   PTYs: 7
#   File Descriptors: 200
#   Age: 35 minutes
#
# ⚠️  Warnings:
#   • High command count (38, threshold: 30)
#   • PTY count elevated (7, threshold: 6)
#
# 💡 Recommendations:
#   • Session is degraded - rotation recommended
#   • Rotate session before reaching 50 commands
#   • Use explicit Python paths to reduce subprocess spawning
```

**JSON Output** (for agents):
```bash
planloop monitor bash-health --json

# Parse output to check health_score and status
# Automate rotation decisions based on thresholds
```

**With Explicit Session/PID:**
```bash
planloop monitor bash-health --session-id my-session
planloop monitor bash-health --pid 12345
```

### Rotation Strategy (Coming in Phase 3)

When health score drops below 50:
```bash
# Manual rotation (current workaround):
# 1. Note your current work
# 2. Create fresh bash session with new ID: sessionId=f"work_{int(time.time())}"
# 3. Continue work in new session

# Automatic rotation (Phase 3 - in development):
# planloop rotate bash-session
# Returns new session ID automatically
```

### Best Practices to Extend Session Life

1. **Use alternative tools when possible:**
   ```bash
   # ❌ Avoid: bash("cat file")
   view("/path/to/file")
   
   # ❌ Avoid: bash("echo content > file")  
   create("/path/to/file", "content")
   
   # ❌ Avoid: bash("grep pattern file")
   grep(pattern="text", path="/path")
   ```

2. **Use explicit Python paths** (reduces subprocess spawning):
   ```bash
   # ❌ Avoid: bash("source .venv && python script.py")
   # ✅ Better: bash(".venv/bin/python script.py")
   ```

3. **Chain commands efficiently**:
   ```bash
   # ❌ Avoid: Multiple bash calls
   bash("cd /path")
   bash("ls -la")
   
   # ✅ Better: Single command
   bash("cd /path && ls -la")
   ```

4. **Monitor proactively**: Don't wait for failures - check health regularly

### Integration with Planloop Workflow

**Agents should check health:**
- After every 10-15 bash commands
- Before long-running operations (tests, builds)
- When bash commands start behaving strangely
- If `next_action` suggests health check (future feature)

**Example autonomous workflow:**
```python
# Pseudo-code for agent integration
command_count = 0

for task in tasks:
    # Check health every 10 commands
    if command_count % 10 == 0:
        health = check_bash_health()
        if health["health_score"] < 50:
            rotate_session()
            command_count = 0
    
    # Execute task
    run_task(task)
    command_count += count_bash_commands_in_task(task)
```

### Research & Background

Full research document: `/Users/honk/code/planloop/tmp/pty-cli-agent-comprehensive-research.md`

**Key Findings:**
- Industry-wide problem affecting VS Code, JetBrains, all node-pty users
- Root cause: File descriptor + PTY resource exhaustion
- Solution: Proactive monitoring + automatic rotation
- Based on RED/USE observability metrics from production systems

**References:**
- GitHub Issue: microsoft/node-pty #670
- Stack Overflow: "posix_spawnp failed opening many terminals"
- Production patterns: Session rotation, health scoring, observability

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

# planloop Agent Instructions
<!-- PLANLOOP-INSTALLED v2.0 -->

## Goal Prompt
# planloop Goal Prompt

You are preparing instructions for an AI coding agent that will use
`planloop` to implement a project. Respond with:

1. **Summary** – One paragraph that restates the goal, success criteria, and
   notable constraints (platforms, deadlines, CI requirements, stakeholders).
2. **Signals** – Bulleted list of known blockers/risk signals. Include CI or
   lint references when provided. If none exist, write `- None reported`.
3. **Initial Tasks** – Numbered list of commit-sized tasks that follow the
   planloop workflow (TDD, small increments, green tests). Each task should
   include:
   - short imperative title,
   - success definition or exit criteria,
   - obvious dependencies on earlier tasks.
4. **Open Questions** – Any clarifications the agent should raise before
   coding (optional).

Keep the response under 350 words. Use concise Markdown and avoid code unless
the user explicitly asks for scaffolding.


## Handshake
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


## Summary Prompt
# planloop Summary Prompt

Produce the final wrap-up for a session when all tasks and signals are closed.
Include the following sections:

1. **Completion Summary** – 2–3 sentences describing the overall result,
   referencing key features or fixes delivered. Mention the test suite / CI
   status.
2. **Task Outcomes** – Bulleted list highlighting each task ID and whether it
   shipped, was skipped, or changed scope.
3. **Signals Resolved** – Bullets referencing any CI/lint/system signals that
   were opened during the session and how they were addressed.
4. **Risks / Follow-ups** – Items that should become future tasks (if empty,
   write `- None`).

Keep the tone factual and reference file paths or PR numbers when relevant.


## Reuse Template Prompt
# planloop Template Reuse Prompt

You are preparing context so a new planloop session can reuse a past template.
Respond with:

1. **Why this template** – 1–2 sentences describing what makes the referenced
   session a good example (tech stack, workflow style, test strategy).
2. **Key Tasks to Mirror** – Bullet list summarizing 3–5 tasks from the
   template that the next agent should follow, with short rationale for each.
3. **Adjustments Needed** – Bullet list describing what must change to adapt
   the template to the new goal (optional if nothing differs).

Use short Markdown bullets and avoid copying large diffs; the goal is to give
the next agent a crisp recipe inspired by the previous success.

