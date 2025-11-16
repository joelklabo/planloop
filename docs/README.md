# Documentation Directory

This directory contains all planloop documentation organized by purpose.

## Structure

### `/docs/agents.md`
The agent workflow contract and command reference. This is the primary guide for AI agents working on planloop. Generated/updated via `planloop guide --target agents-md --apply`.

### `/docs/plans/`
Active implementation plans and task backlogs.

- **`plan.md`** - The canonical v1.5+ implementation backlog. All tasks, milestones, dependencies, and completion status live here. Update this before and after every commit.

### `/docs/reference/`
Reference documents for research, design decisions, and historical information.

- **`multi-agent-research.md`** - Queue fairness design notes, telemetry details, and multi-agent coordination patterns for v1.6+
- **`prompt_lab_results.md`** - Baseline compliance results from automated prompt lab runs
- **`prompt_lab_run_report.md`** - Detailed history of lab runs documenting adapter evolution and compliance improvements

## Navigation

- Start with `agents.md` for workflow rules
- Check `plans/plan.md` for current tasks and implementation status
- Reference `reference/` documents when working on related features or investigating design decisions
