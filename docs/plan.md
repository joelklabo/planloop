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

### Phase 1: Automated Plan Decomposition (Priority: High)
**Goal**: Enable `planloop` to autonomously generate a high-quality, validated task plan from a user's goal using an internal, configurable LLM client. This simplifies the agent workflow by removing the "plan decomposition" meta-task.

**Tasks**:
- [ ] **P1.1**: Extend `config.yml` to securely manage LLM settings (provider, API key, model).
- [ ] **P1.2**: Implement an internal LLM client, starting with OpenAI.
- [ ] **P1.3**: Integrate the client into `planloop start` to generate a task plan from a user's `--goal`.
- [ ] **P1.4**: Implement "Plan Quality Gates" to automatically validate the LLM-generated plan upon creation.
- [ ] **P1.5**: Design the "Plan Decomposition Prompt" (internal to `planloop`).
- [ ] **P1.6**: Design the "LLM-as-a-Judge" Prompt (internal to `planloop`).
- [ ] **P1.7**: Implement the dynamic `agent_instructions` field in the `planloop status` response.
- [ ] **P1.8**: Update documentation (`agent-workflow-visualization.md`, `api-contract.md`, `planning-guide.md`) to reflect the new, simpler onboarding flow and prompt strategy.

---

### Phase 2: Prompt Engineering & Evaluation (Priority: High)
**Goal**: Build a systematic, data-driven process for evaluating and improving the quality of all internal LLM prompts.

**Tasks**:
- [ ] **P2.1**: Build a "Golden Dataset" of evaluation cases (`spec.md` -> `expected_plan.json`).
- [ ] **P2.2**: Define objective metrics for scoring plan quality (e.g., Task Recall, Hint Accuracy).
- [ ] **P2.3**: Create an "Automated Evaluation Harness" script to run prompts against the dataset and generate performance reports.
- [ ] **P2.4**: Document the "Hypothesize -> Edit -> Evaluate -> Analyze" loop for prompt improvement.

---

### Phase 3: Agent Performance (Priority: Critical)
**Goal**: Reach 60%+ baseline compliance for all agents

**Current Status**:
- ✅ Copilot (gpt-5): 64.3% - Target achieved
- ⏳ Claude (sonnet): 46.2% pass rate - Needs +13.8% improvement
- ⏳ OpenAI: 5.7% pass rate - Needs +54.3% improvement

**Tasks**:
- [✅] **P3.1**: Optimize Claude prompts (target 60%+ pass rate) - commit 3b60c7b
- [❌] **P3.2**: Optimize OpenAI prompts (target 60%+ pass rate) - *Deprioritized, focusing on Copilot.*
- [✅] **P3.3**: Document successful prompt patterns per agent - commit 9fdf7a5
- [✅] **P3.4**: Implement regression protection for Copilot baseline - commit e24e2a5
- [✅] **P3.5**: Create agent-specific prompt variations if needed - commit 9a56d6c

**Tools**: `labs/optimize_safely.sh`, `labs/check_baseline.sh`

---

### Phase 4: Advanced Testing Scenarios (Priority: High)
**Blocked Until**: All agents reach 60%+ baseline

**Tasks**:
- [ ] **P4.1**: Implement multi-signal-cascade scenario (5 tasks, 3 signals)
- [ ] **P4.2**: Implement dependency-chain scenario (complex dependencies)
- [ ] **P4.3**: Implement full-plan-completion scenario (12-task feature)
- [ ] **P4.4**: A/B test prompt variations across agents
- [ ] **P4.5**: Document cross-agent prompt patterns

---

### Phase 5: Analytics & Monitoring (Priority: Medium)
**Goal**: Improve visibility into agent performance and system health

**Tasks**:
- [ ] **P5.1**: Session analytics dashboard
  - Task completion times
  - Agent performance by task type
  - Success/failure patterns
- [ ] **P5.2**: Lock queue metrics and tuning
  - Wait time analytics
  - Queue fairness verification
  - Performance under contention
- [ ] **P5.3**: Performance profiling for large plans
  - Benchmark plans with 50+ tasks
  - Identify bottlenecks
  - Optimize compute_now() for scale

---

### Phase 6: Advanced Features (Priority: Low)
**Goal**: Enhance agent capabilities and developer experience

**Tasks**:
- [ ] **P6.1**: Task dependency visualization
  - Generate dependency graphs
  - Identify critical paths
  - Visual plan representation
- [ ] **P6.2**: `planloop inject` interactive decomposition
  - Break down complex tasks
  - Generate subtasks interactively
  - Validate dependencies
- [ ] **P6.3**: Embeddings-based semantic code search
  - Vector search for similar code patterns
  - Enhance suggest with semantic understanding
  - Find related implementations
- [ ] **P6.4**: Learning from suggestion feedback
  - Track accepted/rejected suggestions
  - Improve suggestion quality over time
  - Personalize to team preferences

---

### Future Research (v1.8+)
- **Adapting to In-Flight Goal Changes**: A `planloop revise` command to update a plan when the original spec changes mid-project.
- **Human-in-the-Loop (HITL) Collaboration**: A `human_intervention_required` state to allow the agent to ask for help when conceptually stuck.
- **Shell Command Execution Policy**: A formal policy and safety mechanism for agents running shell commands.
- **Formal Artifact Tracking**: A system for agents to report and track non-code artifacts (e.g., diagrams, reports) they produce.
- **Self-Bootstrapping Agent Instructions**: Ensure agents always have the latest workflow contract by making the synchronization of `agents.md` the implicit first task of any new session.
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
- **`api-contract.md`** - Defines the precise JSON structures for messages exchanged between `planloop` and AI agents.
- **`planning-guide.md`** - Principles and best practices for creating high-quality, actionable task lists.
- **`prompt-and-instruction-catalog.md`** - A comprehensive catalog of all internal prompts and agent-facing instructions.
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