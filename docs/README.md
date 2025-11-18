# Documentation

## Core Documents

### `agents.md`
Agent workflow contract and command reference. This is the primary instruction set for AI agents (Claude, Copilot, etc.). Symlinked to root as `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`.

### `plan.md`
Current development plan and backlog. Living document tracking what's built, active work, and future tasks.

### `architecture.md`
System design reference. High-level overview of core philosophy, state management, locking, and LLM integration.

### `development-setup.md`
Quick reference for setting up the development environment (Python 3.11+, uv, venv).

---

## Dev Mode & Observability

### `dev-mode-observability-plan.md`
Comprehensive specification for development mode with maximum observability. Includes:
- Phase 1A: 4 critical debugging features (error context, lock logging, performance spans, trace linking)
- Complete implementation code examples
- API and web UI plans

### `dev-mode-quick-reference.md`
Implementation checklist, debugging workflows, and success criteria for dev mode. Includes executive summary of expected impact.

---

## Case Studies

### `honk-case-study.md`
Real-world experience using planloop to build the Honk iOS project. Documents what worked, blockers encountered, and feature requests with timeline estimates.

---

## Testing

### `lab-testing.md`
Testing infrastructure guide. Explains test scenarios, how to run labs, and interpret results.

### `agent-performance.md`
Auto-generated performance metrics by model/agent. Updated by test runs.

---

## Reference

### `reference/prompting-guide.md`
Comprehensive prompting guide including:
- Best practices by model (Claude, GPT, etc.)
- Successful patterns library
- Agent-specific variations
- Baseline regression protection strategies

### `reference/agent-testing-reference.md`
Technical testing methodology: output capture methods, comparison techniques.

---

## Archive

Historical documents preserved for reference:
- `archive/v1.5-implementation-tasks.md` - v1.5 task tracking
- `archive/v1.6-suggest-implementation-plan.md` - Suggest feature implementation plan

---

## Document Count

**Before consolidation:** 19 files (~177KB)  
**After consolidation:** 14 files (~155KB)  
**Savings:** 5 files, ~22KB

### Changes Made (2025-11-18)

1. ✅ **Consolidated Honk docs** - Merged `honk-workflow-analysis.md` + `honk-implementation-fixes.md` → `honk-case-study.md`
2. ✅ **Consolidated prompt docs** - Merged 4 reference docs → `reference/prompting-guide.md`
3. ✅ **Merged dev mode docs** - Combined `dev-mode-summary.md` into `dev-mode-quick-reference.md`

**Result:** Cleaner structure, eliminated duplication, maintained all content.
