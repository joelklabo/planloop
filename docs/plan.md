# planloop Development Plan

**Last Updated**: 2025-11-17
**Version**: 1.7 (Active Development)

---

## ✅ What's Built

### v1.6: Code-Aware Task Suggestions
- **`planloop suggest`**: AI-powered codebase analysis for proactive task discovery.
- **LLM Abstraction**: Support for OpenAI, Anthropic, and local models.
- **Context Engine**: Analyzes file structure, git history, and TODOs to inform suggestions.
- **Agent Discoverability**: Hints in `planloop status` guide agents to find new work.

### v1.5: Core Loop & Session Management
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
- ⏳ **Copilot (gpt-5)**: 58.3% pass rate - Needs +1.7% improvement
- ⏳ **Claude (sonnet)**: 46.2% pass rate - Needs +13.8% improvement
- ⏳ **OpenAI**: 33.3% pass rate - Needs +27% improvement

**Next Steps**:
1. Optimize Claude/OpenAI prompts to reach 60%+ baseline
2. Once solid, implement harder test scenarios:
   - `multi-signal-cascade` - 5 tasks, 3 signals at different stages
   - `dependency-chain` - Complex task dependencies
   - `full-plan-completion` - 12-task realistic feature implementation
3. Document successful prompt patterns across all agents

**See**: `lab-testing.md` for testing infrastructure details

---

## 📋 v1.7 Priorities: Quality & Usability

### Phase 1: Agent Performance (Priority: Critical)
**Goal**: Reach 60%+ baseline compliance for all agents

**Current Status**:
- ✅ Copilot (gpt-5): 64.3% - Target achieved
- ⏳ Claude (sonnet): 46.2% pass rate - Needs +13.8% improvement
- ⏳ OpenAI: 5.7% pass rate - Needs +54.3% improvement

**Tasks**:
- [✅] **P1.1**: Optimize Claude prompts (target 60%+ pass rate) - commit 3b60c7b
- [❌] **P1.2**: Optimize OpenAI prompts (target 60%+ pass rate) - *Deprioritized, focusing on Copilot.*
- [✅] **P1.3**: Document successful prompt patterns per agent - commit 9fdf7a5
- [✅] **P1.4**: Implement regression protection for Copilot baseline - commit e24e2a5
- [✅] **P1.5**: Create agent-specific prompt variations if needed - commit 9a56d6c

**Tools**: `labs/optimize_safely.sh`, `labs/check_baseline.sh`

---

### Phase 2: Advanced Testing Scenarios (Priority: High)
**Blocked Until**: All agents reach 60%+ baseline

**Tasks**:
- [ ] **P2.1**: Implement multi-signal-cascade scenario (5 tasks, 3 signals)
- [ ] **P2.2**: Implement dependency-chain scenario (complex dependencies)
- [ ] **P2.3**: Implement full-plan-completion scenario (12-task feature)
- [ ] **P2.4**: A/B test prompt variations across agents
- [ ] **P2.5**: Document cross-agent prompt patterns

---

### Phase 3: Analytics & Monitoring (Priority: Medium)
**Goal**: Improve visibility into agent performance and system health

**Tasks**:
- [ ] **P3.1**: Session analytics dashboard
  - Task completion times
  - Agent performance by task type
  - Success/failure patterns
- [ ] **P3.2**: Lock queue metrics and tuning
  - Wait time analytics
  - Queue fairness verification
  - Performance under contention
- [ ] **P3.3**: Performance profiling for large plans
  - Benchmark plans with 50+ tasks
  - Identify bottlenecks
  - Optimize compute_now() for scale

---

### Phase 4: Advanced Features (Priority: Low)
**Goal**: Enhance agent capabilities and developer experience

**Tasks**:
- [ ] **P4.1**: Task dependency visualization
  - Generate dependency graphs
  - Identify critical paths
  - Visual plan representation
- [ ] **P4.2**: `planloop inject` interactive decomposition
  - Break down complex tasks
  - Generate subtasks interactively
  - Validate dependencies
- [ ] **P4.3**: Embeddings-based semantic code search
  - Vector search for similar code patterns
  - Enhance suggest with semantic understanding
  - Find related implementations
- [ ] **P4.4**: Learning from suggestion feedback
  - Track accepted/rejected suggestions
  - Improve suggestion quality over time
  - Personalize to team preferences

---

### Future Research (v1.8+)
- **Self-Bootstrapping Agent Instructions**: Ensure agents always have the latest workflow contract by making the synchronization of `agents.md` the implicit first task of any new session. The `planloop status` command would detect an out-of-sync `agents.md` and return a `sync_instructions` reason, prompting the agent to update its own rulebook before proceeding.
- **Embeddings-based search**: Use vector DB for semantic code search
- **Learning from feedback**: Track accepted/rejected suggestions to improve quality
- **Batch workflows**: `planloop suggest --weekly` for regular audits
- **Custom analyzers**: Plugin system for domain-specific patterns
- **Diff suggestions**: "This PR introduces X, suggest follow-up tasks"
- **Advanced Analysis**:
  - Test coverage gap analysis (e.g., via `pytest-cov`)
  - Security pattern detection (e.g., via `bandit`, `semgrep`)
  - Performance profiling to suggest optimization tasks
  - Automated dependency update suggestions
- **Multi-agent collaboration patterns**
- **Natural language plan editing**
- **Integration with GitHub Issues/PRs**
- **Plan templates and best practices library**
- **Real-time agent coordination dashboard

---

## 📚 Documentation

### For AI Agents
- **`agents.md`** - Workflow contract and command reference (symlinked to AGENTS.md, CLAUDE.md, .github/copilot-instructions.md)

### Reference
- **`lab-testing.md` - Testing infrastructure, scenarios, evaluation metrics
- **`architecture.md`** - System design, queue fairness, state management
- **`agent-workflow-visualization.md`** - Diagram of the core agent-CLI interaction loop
- **`agent-performance.md`** - Auto-generated test metrics (latest results)

### Archive
- This section is reserved for historical plans and completed task lists.

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