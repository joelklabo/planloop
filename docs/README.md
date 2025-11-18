# Documentation

All planloop documentation for humans and AI agents.

---

## Core Documents

### `agents.md`
**Agent workflow contract** - Primary guide for AI agents. Command reference, workflow rules, and project organization.

**Symlinked to**:
- `AGENTS.md` (root)
- `CLAUDE.md` (root)
- `.github/copilot-instructions.md` (GitHub Copilot)

Updated via: `planloop guide --target agents-md --apply`

### `plan.md`
**Development plan** - Current work, active goals, backlog. What's built (v1.5 complete), what's in progress (agent testing), what's next (v1.6+).

### `architecture.md`
**System design reference** - State management, locking, queue fairness, session lifecycle, command system, testing infrastructure.

### `lab-testing.md`
**Testing guide** - Agent testing infrastructure, scenarios, evaluation metrics, running tests, optimization strategy.

### `agent-performance.md`
**Test metrics** (auto-generated) - Latest agent compliance scores. Updated by `labs/generate_viz.py`.

### `honk-workflow-analysis.md`
**Real-world workflow analysis** - Deep analysis of using planloop to manage honk development. Simulates actual workflow experience with concrete examples.

### `honk-implementation-fixes.md`
**Fixes needed for honk** - Prioritized list of planloop improvements needed to support honk development workflow effectively.

---

## Reference

### `reference/agent-testing-reference.md`
Quick reference for testing agents - output capture, authentication, debugging, common issues.

### `reference/prompt-optimization.md`
Best practices for prompting different AI agents (Claude, Copilot, OpenAI).

---

## Archive

### `archive/v1.5-implementation-tasks.md`
Historical record of all 46 v1.5 implementation tasks with commit SHAs. Complete but kept for reference.

---

## Quick Start

**For AI Agents**:
1. Read `agents.md` for workflow rules
2. Check `plan.md` for current work
3. Reference `architecture.md` when needed

**For Testing**:
- See `lab-testing.md` for testing workflow

**For Development**:
- Check `plan.md` active work section
- Run tests: `pytest tests/`
- Update metrics: `./labs/run_iterations.sh`

---

## Conventions

- **Naming**: All markdown files use `lowercase-with-hyphens.md` (except AGENTS.md, CLAUDE.md symlinks)
- **Temp files**: Use `tmp/` folder at project root (gitignored)
- **Structure**: Flat in `docs/`, archive in `docs/archive/`
