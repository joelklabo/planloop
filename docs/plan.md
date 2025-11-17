# planloop Development Plan

**Last Updated**: 2025-11-17

---

## ✅ What's Built (v1.5 - Complete)

All 46 implementation tasks completed. Full task breakdown in `archive/v1.5-implementation-tasks.md`.

### Core Features
- **Session Management** - Create, list, navigate sessions with `PLANLOOP_HOME`
- **State System** - `state.json` + `PLAN.md` with validation and compute_now logic
- **Locking** - File-based locks with queue fairness, deadlock detection
- **CLI Commands** - `status`, `update`, `alert`, `describe`, `search`, `reuse`, etc.
- **Safe Modes** - Dry-run, no-plan-edit, strict validation for updates
- **History** - Git-based snapshots with `snapshot`/`restore` commands
- **Self-tests** - Automated harness for CI/lint/dependency scenarios
- **Agent Prompts** - Handshake, goal, summary, reuse template generation
- **Queue Fairness** - Multi-agent coordination with FIFO queueing and stall detection
- **Dashboards** - TUI (`view`) and web (`web`) for read-only status

### Architecture
- Python 3.11+ with Typer CLI framework
- Pydantic models with JSON schema validation
- File-based state (no database required)
- Git-based history (optional)

---

## 🎯 Active Work

### Lab Testing & Agent Optimization
**Goal**: Achieve 60%+ baseline compliance across all major AI agents

**Status** (158 runs as of 2025-11-17):
- ✅ **Copilot (gpt-5)**: 64.3% pass rate - Target achieved!
- ⏳ **Claude (sonnet)**: 29.3% pass rate - Needs prompt optimization
- ⏳ **OpenAI**: 33.3% pass rate - Needs prompt optimization

**Next Steps**:
1. Optimize Claude/OpenAI prompts to reach 60%+ baseline
2. Once solid, implement harder test scenarios:
   - `multi-signal-cascade` - 5 tasks, 3 signals at different stages
   - `dependency-chain` - Complex task dependencies
   - `full-plan-completion` - 12-task realistic feature implementation
3. Document successful prompt patterns across all agents

**See**: `lab-testing.md` for testing infrastructure details

---

## 📋 Backlog (v1.6+)

### Testing
- [ ] Implement multi-signal-cascade scenario
- [ ] Implement dependency-chain scenario  
- [ ] Implement full-plan-completion scenario
- [ ] A/B test prompt variations
- [ ] Cross-agent prompt pattern documentation

**Blocked Until**: All agents reach 60%+ baseline on `cli-basics`

### Future Features
- [ ] Task dependency visualization
- [ ] Session analytics/telemetry dashboard
- [ ] Lock queue metrics and tuning
- [ ] Advanced multi-agent coordination patterns
- [ ] Performance profiling for large plans

---

## 📚 Documentation

### For AI Agents
- **`agents.md`** - Workflow contract and command reference (symlinked to AGENTS.md, CLAUDE.md, .github/copilot-instructions.md)

### Reference
- **`lab-testing.md`** - Testing infrastructure, scenarios, evaluation metrics
- **`architecture.md`** - System design, queue fairness, state management
- **`agent-performance.md`** - Auto-generated test metrics (latest results)

### Archive
- **`archive/v1.5-implementation-tasks.md`** - All 46 completed v1.5 tasks with commit SHAs

---

## 🔄 Workflow

When working on planloop:
1. Check **Active Work** section above for current priorities
2. Reference `agents.md` for workflow rules and commands
3. Run tests: `pytest tests/`
4. Update lab metrics: `./labs/run_iterations.sh N SCENARIO AGENTS`
5. Keep this file updated with progress

### Contributing
- Practice TDD: write/update tests first
- Commit often: keep changesets small and focused
- Never commit failing tests
- Update this plan when completing work or adding new tasks
