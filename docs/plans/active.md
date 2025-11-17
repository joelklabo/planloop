# Active Development Plan

**Version**: 1.6-next  
**Status**: Planning  
**Last Updated**: 2025-11-17

## Current Status

✅ **v1.5 Complete** - All core planloop features implemented and tested
- Session management, locking, signals, CLI commands
- Queue fairness with deadlock detection
- Agent prompt infrastructure
- See `docs/reference/v1.5-implementation-complete.md` for full details

## Active Work

### Lab Testing & Optimization
**Status**: In Progress  
**Goal**: Achieve 60%+ baseline compliance across all major AI agents

**Current Metrics** (2025-11-17, 158 runs):
- Copilot (gpt-5): 64.3% pass rate ✅ **Target achieved**
- Claude (sonnet): 29.3% pass rate ⏳ Needs optimization
- OpenAI: 33.3% pass rate ⏳ Needs optimization

**Next Actions**:
1. Optimize Claude prompts to reach 60%+ (currently ~30%)
2. Test additional scenarios when baseline solid across agents
3. Document successful prompt patterns

See `docs/reference/lab-testing-guide.md` for testing workflow.

## Backlog

### Harder Test Scenarios
- [ ] `multi-signal-cascade` - 5 tasks, 3 signals at different stages
- [ ] `dependency-chain` - Complex task dependencies
- [ ] `full-plan-completion` - Realistic 12-task feature workflow

**Blocked Until**: Claude reaches 60%+ baseline on `cli-basics`

### Future Enhancements (v1.6+)
- Advanced queue fairness improvements (see `docs/reference/multi-agent-research.md`)
- Task dependency visualization
- Session analytics/telemetry
- Multi-agent coordination patterns

## Quick Links

- **Agent Guide**: `docs/agents.md` - Workflow contract for AI agents
- **Lab Testing**: `docs/reference/lab-testing-guide.md` - Testing infrastructure
- **Performance Data**: `docs/agent-performance.md` - Latest metrics (auto-generated)
- **v1.5 History**: `docs/reference/v1.5-implementation-complete.md` - Completed implementation tasks

## Workflow

When working on planloop:
1. Check this plan for active work
2. Reference `docs/agents.md` for agent workflow rules
3. Run tests: `pytest tests/`
4. Update metrics: `./labs/run_iterations.sh` for agent testing
5. Keep this file updated with progress
