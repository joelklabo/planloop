# planloop Development Plan

**Last Updated**: 2025-11-18
**Version**: 1.7 (Active Development)

---

## ✅ What's Built

### v1.6: Code-Aware Task Suggestions
- **`planloop suggest`**: AI-powered codebase analysis for proactive task discovery
- **LLM Abstraction**: Support for OpenAI, Anthropic, and local models
- **Context Engine**: Analyzes file structure, git history, and TODOs to inform suggestions
- **Agent Discoverability**: Hints in `planloop status` guide agents to find new work

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

## 📋 All Tasks

### Critical Priority (Blocking Production)

- [ ] **T001**: Fix agent stopping after first task completion
  - **Type**: fix | **Priority**: CRITICAL
  - **Issue**: Agents complete one task then wait for guidance instead of continuing
  - **Impact**: Breaks autonomous multi-task workflow
  - **Solution**: Enhance agents.md instructions, add explicit "next_action" in status JSON
  - **Deliverable**: Updated docs/agents.md with clearer continuation instructions

- [ ] **T002**: Add agent continuation mechanism
  - **Type**: feature | **Priority**: CRITICAL
  - **Issue**: planloop knows task completed but can't proactively signal agent
  - **Solution**: Add "transition_detected" + "suggested_action" to status response
  - **Design**: Detect IN_PROGRESS→DONE transition, include next task details
  - **Deliverable**: Modified src/planloop/commands/status.py (~50 lines)

- [✅] **T003**: Implement structured agent interaction logging
  - **Type**: feature | **Priority**: CRITICAL | **Status**: DONE
  - **Features**: log_agent_command(), log_agent_response(), `planloop logs` command
  - **Location**: src/planloop/dev_mode/agent_transcript.py

### High Priority (Core Functionality)

- [ ] **T004**: Add distributed tracing system
  - **Type**: feature | **Priority**: HIGH
  - **Goal**: Link all operations (errors, LLM calls, state diffs, performance) via trace_id
  - **Solution**: Trace ID generation/propagation (contextvars), format tr_{timestamp}_{random}
  - **Deliverable**: src/planloop/dev_mode/observability.py (~75 lines)

- [ ] **T005**: Implement error context capture
  - **Type**: feature | **Priority**: HIGH
  - **Goal**: When errors occur, capture full debugging context automatically
  - **Solution**: Decorator @capture_error_context(session_dir), captures local variables, stack trace, state snapshot, trace_id
  - **Deliverable**: src/planloop/dev_mode/error_context.py (~150 lines)
  - **Depends on**: T004

- [ ] **T006**: Add lock operation instrumentation
  - **Type**: feature | **Priority**: HIGH
  - **Goal**: Debug multi-agent contention and deadlocks
  - **Solution**: Log all lock operations (request, acquire, release), track wait time, hold time, operation name, entry_id
  - **Deliverable**: Modified src/planloop/core/lock.py (~50 lines)

- [ ] **T007**: Fix agents.md synchronization in workflow
  - **Type**: fix | **Priority**: HIGH
  - **Issue**: `planloop guide --apply` doesn't update after marker exists (guide.py:40-41)
  - **Impact**: Agents work with stale instructions
  - **Solution**: Add version to marker, enable updates when prompts change

- [ ] **T008**: Fix uv dependency sync after Rust/pyproject.toml changes
  - **Type**: fix | **Priority**: HIGH
  - **Issue**: uv fails when pydantic-core (requires Rust) is updated
  - **Impact**: Breaks dev environment, blocks agents
  - **Solution**: Document Rust requirements, add checks to verify-env.sh, retry logic

### Medium Priority (Quality & Testing)

- [ ] **T009**: Implement performance span tracing
  - **Type**: feature | **Priority**: MEDIUM
  - **Goal**: Break down operation time (LLM vs I/O vs parsing)
  - **Solution**: Context manager with trace_span(name, **metadata), tracks duration_ms
  - **Deliverable**: src/planloop/dev_mode/spans.py (~150 lines)
  - **Depends on**: T004

- [ ] **T010**: Enforce TDD workflow in agent instructions
  - **Type**: chore | **Priority**: MEDIUM
  - **Issue**: Agents skip TDD despite workflow contract
  - **Impact**: Poor test coverage, quality issues
  - **Solution**: Make TDD prominent in agents.md, add checklist to status, include examples

- [ ] **T011**: Implement multi-signal-cascade scenario
  - **Type**: test | **Priority**: MEDIUM
  - **Goal**: Test agents with complex workflows (5 tasks, 3 signals at stages)
  - **Blocked until**: T001, T002, T007, T008 complete

- [ ] **T012**: Implement dependency-chain scenario
  - **Type**: test | **Priority**: MEDIUM
  - **Goal**: Test complex task dependencies
  - **Blocked until**: T001, T002, T007, T008 complete

- [ ] **T013**: Implement full-plan-completion scenario
  - **Type**: test | **Priority**: MEDIUM
  - **Goal**: Test 12-task feature implementation end-to-end
  - **Blocked until**: T001, T002, T007, T008 complete

- [ ] **T014**: A/B test prompt variations across agents
  - **Type**: test | **Priority**: MEDIUM
  - **Blocked until**: T001, T002, T007, T008 complete

- [ ] **T015**: Document cross-agent prompt patterns
  - **Type**: chore | **Priority**: MEDIUM
  - **Blocked until**: T014 complete

- [✅] **T016**: Optimize Claude prompts (target 60%+ pass rate)
  - **Type**: test | **Priority**: MEDIUM | **Status**: DONE
  - **Commit**: 3b60c7b

- [❌] **T017**: Optimize OpenAI prompts (target 60%+ pass rate)
  - **Type**: test | **Priority**: MEDIUM | **Status**: DEPRIORITIZED

- [✅] **T018**: Document successful prompt patterns per agent
  - **Type**: chore | **Priority**: MEDIUM | **Status**: DONE
  - **Commit**: 9fdf7a5

- [✅] **T019**: Implement regression protection for Copilot baseline
  - **Type**: test | **Priority**: MEDIUM | **Status**: DONE
  - **Commit**: e24e2a5

- [✅] **T020**: Create agent-specific prompt variations if needed
  - **Type**: test | **Priority**: MEDIUM | **Status**: DONE
  - **Commit**: 9a56d6c

### Website: Foundation Setup

- [ ] **T021**: Initialize Vite + React + TypeScript project
  - **Type**: chore | **Priority**: LOW
  - **Description**: Create frontend/ directory, run `npm create vite@latest`, configure TypeScript strict mode
  - **Acceptance**: `npm run dev` works, shows React app

- [ ] **T022**: Configure Tailwind CSS v4
  - **Type**: chore | **Priority**: LOW
  - **Description**: Install Tailwind, setup config, add to main.css, test utility classes
  - **Acceptance**: Tailwind classes work in components
  - **Depends on**: T021

- [ ] **T023**: Install and configure Framer Motion
  - **Type**: chore | **Priority**: LOW
  - **Description**: `npm install framer-motion`, create basic animation utilities, test transitions
  - **Acceptance**: Simple fade/slide animation works
  - **Depends on**: T021

- [ ] **T024**: Setup React Router with animated transitions
  - **Type**: feature | **Priority**: LOW
  - **Description**: Install react-router-dom, create route structure, add page transitions with Framer Motion
  - **Acceptance**: Navigation between pages with smooth animations
  - **Depends on**: T021, T023

- [ ] **T025**: Configure FastAPI to serve React build
  - **Type**: chore | **Priority**: LOW
  - **Description**: Update server.py to serve static files from frontend/dist/, add CORS, setup Vite proxy
  - **Acceptance**: FastAPI serves React app in production mode
  - **Depends on**: T021

- [ ] **T026**: Create base layout components
  - **Type**: feature | **Priority**: LOW
  - **Description**: Header, Sidebar, Footer with Tailwind + animations, dark/light theme toggle
  - **Acceptance**: Layout renders on all pages, theme toggle works
  - **Depends on**: T022, T023

### Website: Session Dashboard

- [ ] **T027**: Create REST API endpoints for sessions
  - **Type**: feature | **Priority**: LOW
  - **Description**: GET /api/sessions, GET /api/sessions/:id, GET /api/sessions/:id/tasks, GET /api/sessions/:id/signals
  - **Acceptance**: All endpoints return correct JSON, match Pydantic schemas
  - **Depends on**: T025

- [ ] **T028**: Generate TypeScript types from Pydantic models
  - **Type**: chore | **Priority**: LOW
  - **Description**: Script to auto-generate TS types from SessionState, Task, Signal models
  - **Acceptance**: Types in frontend/src/types/ match backend exactly
  - **Depends on**: T027

- [ ] **T029**: Build sessions list page with animations
  - **Type**: feature | **Priority**: LOW
  - **Description**: Fetch sessions, display as animated card grid, search/filter, session stats
  - **Acceptance**: Sessions render beautifully, cards animate on hover/click
  - **Depends on**: T027, T028

- [ ] **T030**: Build session detail page
  - **Type**: feature | **Priority**: LOW
  - **Description**: Task table, signal indicators, status badges, "now" display, all with animations
  - **Acceptance**: Shows all session data, smooth transitions between states
  - **Depends on**: T027, T028

### Website: Kanban View

- [ ] **T031**: Install and configure dnd-kit
  - **Type**: chore | **Priority**: LOW
  - **Description**: Install @dnd-kit packages, setup sensors (mouse, touch, keyboard), test basic drag-drop
  - **Acceptance**: Can drag test items between containers
  - **Depends on**: T021

- [ ] **T032**: Build Kanban board layout
  - **Type**: feature | **Priority**: LOW
  - **Description**: 3 columns (TODO, IN_PROGRESS, DONE), animated column cards, drag overlay with Framer Motion
  - **Acceptance**: Kanban board renders, columns animate
  - **Depends on**: T031

- [ ] **T033**: Implement drag-drop logic with API updates
  - **Type**: feature | **Priority**: LOW
  - **Description**: Move tasks between columns, POST to update status, optimistic updates, smooth reordering
  - **Acceptance**: Drag-drop works, API updates, animations are smooth (60fps)
  - **Depends on**: T032, T027

- [ ] **T034**: Create animated task card component
  - **Type**: feature | **Priority**: LOW
  - **Description**: Task card with hover effects, click to expand modal, show details/dependencies/labels
  - **Acceptance**: Cards look beautiful, modal animations work
  - **Depends on**: T032

### Website: Real-Time Updates

- [ ] **T035**: Create WebSocket endpoint in FastAPI
  - **Type**: feature | **Priority**: LOW
  - **Description**: /ws/sessions/:id endpoint, broadcast task/signal changes, connection management
  - **Acceptance**: WebSocket connects, receives test messages
  - **Depends on**: T027

- [ ] **T036**: Build useWebSocket React hook
  - **Type**: feature | **Priority**: LOW
  - **Description**: Auto-reconnect, message type handling, error handling, connection status indicator
  - **Acceptance**: Hook connects, reconnects on disconnect, handles errors gracefully
  - **Depends on**: T035

- [ ] **T037**: Integrate real-time task updates in Kanban
  - **Type**: feature | **Priority**: LOW
  - **Description**: Subscribe to task changes, animate task moves from other users, show who's working on what
  - **Acceptance**: Tasks update live across browser tabs, smooth animations
  - **Depends on**: T036, T033

- [ ] **T038**: Integrate real-time signal updates
  - **Type**: feature | **Priority**: LOW
  - **Description**: Live signal badge updates, alert animations, system notifications
  - **Acceptance**: Signals update live, animations fire on changes
  - **Depends on**: T036, T030

### Website: Observability Dashboard

- [ ] **T039**: Create observability API endpoints
  - **Type**: feature | **Priority**: LOW
  - **Description**: GET /api/sessions/:id/logs, GET /api/sessions/:id/traces, GET /api/sessions/:id/errors, GET /api/sessions/:id/llm-calls
  - **Acceptance**: All endpoints return correct data from dev_mode/
  - **Depends on**: T027

- [ ] **T040**: Build logs viewer with search/filter
  - **Type**: feature | **Priority**: LOW
  - **Description**: Display JSONL logs, syntax highlighting, search, real-time streaming
  - **Acceptance**: Can view and search logs easily
  - **Depends on**: T039

- [ ] **T041**: Build traces visualization
  - **Type**: feature | **Priority**: LOW
  - **Description**: Trace timeline, span breakdown, waterfall chart, performance metrics
  - **Acceptance**: Can see trace data visually, identify bottlenecks
  - **Depends on**: T039

- [ ] **T042**: Build errors dashboard
  - **Type**: feature | **Priority**: LOW
  - **Description**: Error list, stack traces, error context, group by trace_id, error rate chart
  - **Acceptance**: Can debug errors effectively with full context
  - **Depends on**: T039

### Website: Feedback System

- [ ] **T042a**: Create feedback API endpoints
  - **Type**: feature | **Priority**: LOW
  - **Description**: Add REST endpoints for feedback data
    - GET /api/sessions/:id/feedback - Retrieve all feedback for a session
    - GET /api/feedback - List all feedback across sessions (with filters)
    - GET /api/feedback/stats - Aggregate feedback statistics
  - **Backend Changes**:
    - Add routes to server.py to read feedback.json from session directories
    - Support filtering by: session, agent, rating, date range, tags
    - Return aggregated stats: avg rating, issue categories, trends over time
  - **Acceptance**: All endpoints return correct JSON, handle missing feedback gracefully
  - **Depends on**: T027

- [ ] **T042b**: Build feedback viewer page
  - **Type**: feature | **Priority**: LOW
  - **Description**: Comprehensive feedback dashboard with multiple views
  - **UI Components**:
    - **Feedback List View**:
      - Chronological list of all feedback entries
      - Filter by session, agent, rating (1-5 stars), date range
      - Search feedback text content
      - Color-coded by rating (red 1-2, yellow 3, green 4-5)
      - Click to expand full details
    - **Feedback Detail Panel**:
      - Full feedback message (supports markdown)
      - Session context: session name, title, task count, completion status
      - Agent metadata: agent name, tasks completed, session duration
      - Timestamp and session link
      - Tags/categories (UX, bugs, documentation, workflow, etc.)
    - **Aggregate Stats Dashboard**:
      - Average rating over time (line chart)
      - Rating distribution (histogram)
      - Top issues by frequency (bar chart)
      - Agent-specific trends (compare agents)
      - Session success rate correlation
  - **Actions Available**:
    - View full session details (link to session detail page)
    - Export feedback to CSV/JSON for analysis
    - Mark feedback as "addressed" or "in progress"
    - Add internal notes/responses to feedback
    - Tag feedback with issue categories
    - Filter by "needs attention" (rating ≤ 2)
  - **Animations**:
    - Smooth transitions between list/detail views
    - Hover effects on feedback cards
    - Loading skeletons while fetching
    - Animated charts with Framer Motion
  - **Acceptance**: 
    - Can view all feedback with rich context
    - Filtering and search work smoothly
    - Charts update reactively
    - Export functions work correctly
  - **Depends on**: T042a, T028

- [ ] **T042c**: Integrate feedback prompts into session detail page
  - **Type**: feature | **Priority**: LOW
  - **Description**: Show feedback requests and existing feedback in session view
  - **Features**:
    - Display feedback_request from status when present
    - Show inline prompt: "Session complete! Please provide feedback"
    - Quick feedback form (inline, no page navigation)
    - Display existing session feedback in collapsible section
    - Visual indicator if session has feedback (badge on session card)
  - **Actions**:
    - Submit feedback directly from session page (POST to CLI via exec)
    - Edit existing feedback (if supported by backend)
    - Quick rating buttons (1-5 stars, one click)
    - Textarea for detailed message
    - Auto-save draft feedback to localStorage
  - **Acceptance**: 
    - Feedback prompts appear when tasks complete
    - Can submit feedback without leaving session page
    - Existing feedback displays beautifully
  - **Depends on**: T030, T042a

- [ ] **T042d**: Add feedback insights to observability dashboard
  - **Type**: feature | **Priority**: LOW
  - **Description**: Correlate feedback with session performance data
  - **Features**:
    - Show feedback rating alongside session metrics
    - Highlight sessions with low ratings in error dashboard
    - Cross-reference feedback with traces/errors/logs
    - Identify patterns: "Low ratings often correlate with X errors"
    - Agent comparison: which agents report most issues?
  - **Visualizations**:
    - Feedback timeline overlaid on trace timeline
    - Error rate vs feedback rating scatter plot
    - "Problematic areas" heatmap (which commands get bad feedback)
  - **Acceptance**: 
    - Can identify root causes from feedback + observability data
    - Insights are actionable for improvements
  - **Depends on**: T042b, T039

### Website: Polish & Production

- [ ] **T043**: Performance optimization
  - **Type**: chore | **Priority**: LOW
  - **Description**: Code splitting, lazy loading, image optimization, bundle analysis, <500KB initial load
  - **Acceptance**: Lighthouse score 90+ on all metrics
  - **Depends on**: T021-T042

- [ ] **T044**: Accessibility improvements
  - **Type**: chore | **Priority**: LOW
  - **Description**: ARIA labels, keyboard navigation, screen reader testing, WCAG AA compliance
  - **Acceptance**: Screen reader works, keyboard nav works, color contrast passes
  - **Depends on**: T021-T042

- [ ] **T045**: Animation polish pass
  - **Type**: chore | **Priority**: LOW
  - **Description**: Smooth all transitions, add loading skeletons, microinteractions, gesture support
  - **Acceptance**: 60fps everywhere, no jank, feels polished
  - **Depends on**: T021-T042

- [ ] **T046**: Production deployment setup
  - **Type**: chore | **Priority**: LOW
  - **Description**: Docker setup, environment config, build optimization, monitoring
  - **Acceptance**: Can deploy to production, monitoring works
  - **Depends on**: T021-T042

### Analytics & Monitoring

- [ ] **T047**: Session analytics dashboard
  - **Type**: feature | **Priority**: LOW
  - **Description**: Task completion times, agent performance by type, success/failure patterns
  - **Integrate with**: T030 (session detail page)

- [ ] **T048**: Lock queue metrics and tuning
  - **Type**: feature | **Priority**: LOW
  - **Description**: Wait time analytics, queue fairness verification, performance under contention

- [ ] **T049**: Performance profiling for large plans
  - **Type**: chore | **Priority**: LOW
  - **Description**: Benchmark plans with 50+ tasks, identify bottlenecks, optimize compute_now()

### Configuration & Environment

- [ ] **T050**: Make suggest task limit configurable
  - **Type**: chore | **Priority**: LOW
  - **Investigation**: Verify default (config says 5, but reports show 10?)
  - **Actions**: Add `--limit` flag if missing, document setting, add validation (min=1, max=50)

- [ ] **T051**: Auto-initialize venv for project sessions
  - **Type**: feature | **Priority**: LOW
  - **Phase 1**: Detect and warn if venv missing (pyproject.toml, requirements.txt, etc.)
  - **Phase 2**: Offer to create venv with user confirmation
  - **Phase 3**: Auto-create for known project types (Python/Node/Ruby)
  - **Challenge**: Can't activate venv for agent, must prefix commands with venv path

### Advanced Features (Backlog)

- [ ] **T052**: Task dependency visualization
  - **Type**: feature | **Priority**: BACKLOG
  - **Description**: Generate dependency graphs, identify critical paths

- [ ] **T053**: `planloop inject` interactive decomposition
  - **Type**: feature | **Priority**: BACKLOG
  - **Description**: Break down complex tasks, generate subtasks, validate dependencies

- [ ] **T054**: Embeddings-based semantic code search
  - **Type**: feature | **Priority**: BACKLOG
  - **Description**: Vector search for patterns, enhance suggest with semantic understanding

---

## 🎨 Website Design System

### Tech Stack
- **Backend**: FastAPI (existing), Python 3.11+
- **Frontend**: React 18+, TypeScript, Vite, Tailwind CSS, Framer Motion, dnd-kit, React Router

### Colors
- **Primary**: Blue (#3b82f6)
- **Success**: Green (#10b981)
- **Warning**: Yellow (#f59e0b)
- **Error**: Red (#ef4444)
- **Task States**: TODO Gray (#6b7280), IN_PROGRESS Blue (#3b82f6), DONE Green (#10b981)

### Animation Timing
- **Fast**: 150ms (button hovers)
- **Medium**: 300ms (page transitions)
- **Slow**: 500ms (drag-drop)
- **Easing**: ease-out (default)

### Spacing
- Consistent 4px grid (Tailwind defaults)
- Card padding: 24px (p-6)
- Section spacing: 32px (space-y-8)

---

## 📚 Documentation

### For AI Agents
- **`agents.md`** - Workflow contract and command reference (symlinked to AGENTS.md, CLAUDE.md, .github/copilot-instructions.md)

### Reference
- **`lab-testing.md`** - Testing infrastructure, scenarios, evaluation metrics
- **`architecture.md`** - System design, queue fairness, state management
- **`agent-workflow-visualization.md`** - Diagram of the core agent-CLI interaction loop
- **`agent-performance.md`** - Auto-generated test metrics (latest results)

### Archive
- **`archive/v1.5-implementation-tasks.md`** - Historical v1.5 task list
- **`archive/v1.6-suggest-implementation-plan.md`** - Historical v1.6 suggest feature plan
- **`archive/dev-mode-observability-plan.md`** - Historical observability planning

---

## 🔄 Workflow

When working on planloop:
1. Check task list above, filter by priority (CRITICAL → HIGH → MEDIUM → LOW)
2. Reference `agents.md` for workflow rules and commands
3. Run tests: `pytest tests/`
4. Update lab metrics: `./labs/run_iterations.sh N SCENARIO AGENTS`
5. Keep this file updated with progress

### Contributing
- Practice TDD: write/update tests first
- Commit often: keep changesets small and focused
- Never commit failing tests
- Update this plan when completing work or adding new tasks

---

## 🚀 Future Research (v1.8+)

Ideas for future exploration once v1.7 stabilizes:
- Self-Bootstrapping Agent Instructions: Auto-sync agents.md at session start
- Test coverage gap analysis: Integrate pytest-cov to suggest missing tests
- Security pattern detection: Integrate bandit/semgrep for security tasks
- Batch workflows: `planloop suggest --weekly` for regular audits
- Custom analyzers: Plugin system for domain-specific patterns
- Diff suggestions: "This PR introduces X, suggest follow-up tasks"
- Multi-agent collaboration: Patterns for multiple agents in same session
- Natural language plan editing: Update plan via conversational interface
- GitHub integration: Sync with Issues/PRs
- Plan templates library: Best practices and starter templates
- Performance profiling: Suggest optimization tasks automatically
