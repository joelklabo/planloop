# planloop Development Plan

**Last Updated**: 2025-11-18
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

### Current Focus: Real-World Agent Issues
**Priority**: Address critical issues discovered during live agent runs before continuing lab optimization.

**Critical Blockers**:
1. **Agent stops after first task** - Need continuation mechanism (P5.1, P5.2)
2. **No agent activity logs** - Can't debug what agents are doing (P5.4)
3. **TDD not being followed** - Code quality impact (P5.3)

**Next**: Once critical fixes are in, return to lab optimization and advanced testing scenarios.

---

## 📋 v1.7 Priorities: Quality & Usability

### Phase 1: Critical Workflow Fixes (Priority: **CRITICAL**)
**Goal**: Fix blocking issues discovered in real agent runs

**Status**: 🚨 **ACTIVE** - These are showstoppers for production use

**Tasks**:
- [ ] **P1.1**: Fix agent stopping after first task completion
  - **Issue**: Agents complete one task then wait for guidance instead of continuing
  - **Impact**: Breaks autonomous multi-task workflow
  - **Solution**: Enhance agents.md instructions, add explicit "next_action" in status JSON
  - **Type**: fix | **Priority**: CRITICAL
  
- [ ] **P1.2**: Add agent continuation mechanism
  - **Issue**: planloop knows task completed but can't proactively signal agent
  - **Solution**: Add "transition_detected" + "suggested_action" to status response
  - **Design**: Detect IN_PROGRESS→DONE transition, include next task details
  - **Type**: feature | **Priority**: CRITICAL

- [ ] **P1.3**: Implement structured agent interaction logging
  - **Issue**: No audit trail of agent commands/responses, valuable context lost in notes
  - **Solution**: JSON Lines transcript at `session_dir/logs/agent-transcript.jsonl`
  - **Features**: log_agent_command(), log_agent_response(), `planloop logs` command
  - **Type**: feature | **Priority**: CRITICAL

- [ ] **P1.4**: Enforce TDD workflow in agent instructions
  - **Issue**: Agents skip TDD despite workflow contract
  - **Impact**: Poor test coverage, quality issues
  - **Solution**: Make TDD prominent in agents.md, add checklist to status, include examples
  - **Type**: chore | **Priority**: HIGH

---

### Phase 2: Essential Bug Fixes (Priority: **HIGH**)
**Goal**: Fix issues that cause workflow failures

**Tasks**:
- [ ] **P2.1**: Fix agents.md synchronization in workflow
  - **Issue**: `planloop guide --apply` doesn't update after marker exists (guide.py:40-41)
  - **Impact**: Agents work with stale instructions
  - **Solution**: Add version to marker, enable updates when prompts change
  - **Type**: fix | **Priority**: HIGH

- [ ] **P2.2**: Fix uv dependency sync after Rust/pyproject.toml changes
  - **Issue**: uv fails when pydantic-core (requires Rust) is updated
  - **Impact**: Breaks dev environment, blocks agents
  - **Solution**: Document Rust requirements, add checks to verify-env.sh, retry logic
  - **Type**: fix | **Priority**: HIGH

---

### Phase 3: Lab Testing & Optimization (Priority: **MEDIUM**)
**Goal**: Achieve 60%+ baseline compliance across all major AI agents

**Status**: ⏸️ **PAUSED** - Resuming after P1-P2 complete

**Current Results** (158 runs as of 2025-11-17):
- ✅ **Copilot (gpt-5)**: 64.3% - Target achieved
- ⏳ **Claude (sonnet)**: 46.2% pass rate - Needs +13.8% improvement
- ⏳ **OpenAI**: 5.7% pass rate - Needs +54.3% improvement

**Tasks**:
- [✅] **P3.1**: Optimize Claude prompts (target 60%+ pass rate) - commit 3b60c7b
- [❌] **P3.2**: Optimize OpenAI prompts (target 60%+ pass rate) - *Deprioritized*
- [✅] **P3.3**: Document successful prompt patterns per agent - commit 9fdf7a5
- [✅] **P3.4**: Implement regression protection for Copilot baseline - commit e24e2a5
- [✅] **P3.5**: Create agent-specific prompt variations if needed - commit 9a56d6c

**Tools**: `labs/optimize_safely.sh`, `labs/check_baseline.sh`

---

### Phase 4: Advanced Testing Scenarios (Priority: **MEDIUM**)
**Goal**: Test agents with complex, realistic workflows

**Blocked Until**: Phase 1-2 complete, Phase 3 at 60%+ baseline

**Tasks**:
- [ ] **P4.1**: Implement multi-signal-cascade scenario (5 tasks, 3 signals at stages)
- [ ] **P4.2**: Implement dependency-chain scenario (complex task dependencies)
- [ ] **P4.3**: Implement full-plan-completion scenario (12-task feature)
- [ ] **P4.4**: A/B test prompt variations across agents
- [ ] **P4.5**: Document cross-agent prompt patterns

---

### Phase 5: Web Interface & Visualization (Priority: **LOW**)
**Goal**: Improve visual feedback for users and agents

**Tasks**:
- [ ] **P5.1**: Implement web dashboard for task visualization
  - **Current**: Basic HTML tables in web/server.py
  - **Requirements**: Kanban/timeline view, task colors, dependency graph, real-time updates
  - **Tech**: FastAPI + HTMX, reuse SessionViewModel
  - **Features**: Session selector, filters, commit links
  - **Type**: feature | **Priority**: LOW

- [ ] **P5.2**: Add pipeline visualization to web dashboard
  - **Requirements**: Horizontal pipeline (TODO → IN_PROGRESS → DONE)
  - **Design**: Task cards, commit SHA on completion, time in each stage
  - **Consider**: Add REVIEW status between IN_PROGRESS and DONE?
  - **Depends on**: P5.1
  - **Type**: feature | **Priority**: LOW

---

### Phase 6: Analytics & Monitoring (Priority: **LOW**)
**Goal**: Improve visibility into agent performance and system health

**Tasks**:
- [ ] **P6.1**: Session analytics dashboard
  - Task completion times, agent performance by type, success/failure patterns
  - Integrate with P5.1 web dashboard
  
- [ ] **P6.2**: Lock queue metrics and tuning
  - Wait time analytics, queue fairness verification, performance under contention
  
- [ ] **P6.3**: Performance profiling for large plans
  - Benchmark plans with 50+ tasks, identify bottlenecks, optimize compute_now()

---

### Phase 7: Configuration & Environment (Priority: **LOW**)
**Goal**: Improve setup and configuration flexibility

**Tasks**:
- [ ] **P7.1**: Make suggest task limit configurable
  - **Investigation**: Verify default (config says 5, but reports show 10?)
  - **Actions**: Add `--limit` flag if missing, document setting, add validation (min=1, max=50)
  - **Type**: chore | **Priority**: LOW

- [ ] **P7.2**: Auto-initialize venv for project sessions
  - **Phase 1**: Detect and warn if venv missing (pyproject.toml, requirements.txt, etc.)
  - **Phase 2**: Offer to create venv with user confirmation
  - **Phase 3**: Auto-create for known project types (Python/Node/Ruby)
  - **Challenge**: Can't activate venv for agent, must prefix commands with venv path
  - **Type**: feature | **Priority**: LOW

---

### Phase 8: Advanced Features (Priority: **BACKLOG**)
**Goal**: Enhance agent capabilities and developer experience

**Tasks**:
- [ ] **P8.1**: Task dependency visualization
  - Generate dependency graphs, identify critical paths
  
- [ ] **P8.2**: `planloop inject` interactive decomposition
  - Break down complex tasks, generate subtasks, validate dependencies
  
- [ ] **P8.3**: Embeddings-based semantic code search
  - Vector search for patterns, enhance suggest with semantic understanding
  
- [ ] **P8.4**: Learning from suggestion feedback
  - Track accepted/rejected suggestions, improve quality over time

---

### Future Research (v1.8+)
**Ideas for future exploration once v1.7 stabilizes**

- **Self-Bootstrapping Agent Instructions**: Auto-sync agents.md at session start
- **Test coverage gap analysis**: Integrate pytest-cov to suggest missing tests
- **Security pattern detection**: Integrate bandit/semgrep for security tasks
- **Batch workflows**: `planloop suggest --weekly` for regular audits
- **Custom analyzers**: Plugin system for domain-specific patterns
- **Diff suggestions**: "This PR introduces X, suggest follow-up tasks"
- **Multi-agent collaboration**: Patterns for multiple agents in same session
- **Natural language plan editing**: Update plan via conversational interface
- **GitHub integration**: Sync with Issues/PRs
- **Plan templates library**: Best practices and starter templates
- **Performance profiling**: Suggest optimization tasks automatically

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