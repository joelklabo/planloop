# Documentation Index

This folder contains all planloop documentation for both humans and AI agents.

## Core Documents

### `agents.md`
The agent workflow contract and command reference. Primary guide for AI agents working on planloop. Generated/updated via `planloop guide --target agents-md --apply`.

**Symlinked to**:
- `AGENTS.md` (root)
- `CLAUDE.md` (root)
- `.github/copilot-instructions.md` (GitHub Copilot)

### `plans/`
Active implementation plans and task backlogs.

- **`active.md`** - Current work and backlog (v1.6+)

### `reference/`
Completed work, research, and technical guides.

- **`v1.5-implementation-complete.md`** - All v1.5 implementation tasks (DONE)
- **`lab-testing-guide.md`** - Agent testing infrastructure and metrics
- **`multi-agent-research.md`** - Queue fairness design notes

### `agent-performance.md`
**Auto-generated** - Latest agent testing metrics (updated by `labs/generate_viz.py`)

## Quick Start

**For AI Agents**:
- Read `agents.md` for workflow rules
- Check `plans/active.md` for current tasks

**For Testing**:
- See `reference/lab-testing-guide.md`

## Conventions

- All markdown files use `lowercase-with-hyphens.md`
- Temporary files go in `tmp/` at project root (gitignored)
