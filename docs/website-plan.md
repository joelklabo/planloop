# Planloop Website Development Plan

**Created**: 2025-11-18  
**Version**: 1.0 (Initial)  
**Stack**: FastAPI + React + TypeScript + Vite + Tailwind + Framer Motion + dnd-kit

---

## 🎯 Mission

Build a modern, beautifully animated web dashboard for planloop with real-time task monitoring, Kanban visualization, and observability features.

---

## ✅ Tech Stack (Research Complete)

**Research Quality**: 9/10 | [Full Research](/tmp/website-plan-research.md)

**Backend**:
- FastAPI (existing) - async, WebSocket support
- Python 3.11+ - matches planloop core

**Frontend**:
- React 18+ - rich UI ecosystem
- TypeScript - type safety
- Vite - instant dev server, fast HMR
- Tailwind CSS - utility-first styling
- Framer Motion - smooth animations
- dnd-kit - modern drag-drop (actively maintained)
- React Router - navigation

**Why This Stack?**
- Modern (2025 best practices)
- Fast development (Vite + Tailwind)
- Beautiful animations (Framer Motion)
- Type-safe (TypeScript + Pydantic)
- Production-ready (used by top companies)

---

## 📋 Tasks

### Phase 1: Foundation Setup
**Goal**: Initialize frontend project with all tools configured

- [ ] **W1.1**: Initialize Vite + React + TypeScript project
  - **Type**: chore
  - **Status**: TODO
  - **Description**: Create frontend/ directory, run `npm create vite@latest`, configure TypeScript strict mode
  - **Acceptance**: `npm run dev` works, shows React app

- [ ] **W1.2**: Configure Tailwind CSS v4
  - **Type**: chore  
  - **Status**: TODO
  - **Description**: Install Tailwind, setup config, add to main.css, test utility classes
  - **Acceptance**: Tailwind classes work in components
  - **Depends on**: W1.1

- [ ] **W1.3**: Install and configure Framer Motion
  - **Type**: chore
  - **Status**: TODO
  - **Description**: `npm install framer-motion`, create basic animation utilities, test transitions
  - **Acceptance**: Simple fade/slide animation works
  - **Depends on**: W1.1

- [ ] **W1.4**: Setup React Router with animated transitions
  - **Type**: feature
  - **Status**: TODO
  - **Description**: Install react-router-dom, create route structure, add page transitions with Framer Motion
  - **Acceptance**: Navigation between pages with smooth animations
  - **Depends on**: W1.1, W1.3

- [ ] **W1.5**: Configure FastAPI to serve React build
  - **Type**: chore
  - **Status**: TODO
  - **Description**: Update server.py to serve static files from frontend/dist/, add CORS, setup Vite proxy
  - **Acceptance**: FastAPI serves React app in production mode
  - **Depends on**: W1.1

- [ ] **W1.6**: Create base layout components
  - **Type**: feature
  - **Status**: TODO
  - **Description**: Header, Sidebar, Footer with Tailwind + animations, dark/light theme toggle
  - **Acceptance**: Layout renders on all pages, theme toggle works
  - **Depends on**: W1.2, W1.3

### Phase 2: Session Dashboard
**Goal**: Display sessions, tasks, and signals with beautiful UI

- [ ] **W2.1**: Create REST API endpoints for sessions
  - **Type**: feature
  - **Status**: TODO
  - **Description**: 
    ```
    GET /api/sessions - List all sessions
    GET /api/sessions/:id - Session details  
    GET /api/sessions/:id/tasks - Tasks list
    GET /api/sessions/:id/signals - Signals list
    ```
  - **Acceptance**: All endpoints return correct JSON, match Pydantic schemas
  - **Depends on**: W1.5

- [ ] **W2.2**: Generate TypeScript types from Pydantic models
  - **Type**: chore
  - **Status**: TODO
  - **Description**: Script to auto-generate TS types from SessionState, Task, Signal models
  - **Acceptance**: Types in frontend/src/types/ match backend exactly
  - **Depends on**: W2.1

- [ ] **W2.3**: Build sessions list page with animations
  - **Type**: feature
  - **Status**: TODO
  - **Description**: Fetch sessions, display as animated card grid, search/filter, session stats
  - **Acceptance**: Sessions render beautifully, cards animate on hover/click
  - **Depends on**: W2.1, W2.2

- [ ] **W2.4**: Build session detail page
  - **Type**: feature
  - **Status**: TODO
  - **Description**: Task table, signal indicators, status badges, "now" display, all with animations
  - **Acceptance**: Shows all session data, smooth transitions between states
  - **Depends on**: W2.1, W2.2

### Phase 3: Kanban View
**Goal**: Beautiful drag-drop Kanban board for task management

- [ ] **W3.1**: Install and configure dnd-kit
  - **Type**: chore
  - **Status**: TODO
  - **Description**: Install @dnd-kit packages, setup sensors (mouse, touch, keyboard), test basic drag-drop
  - **Acceptance**: Can drag test items between containers
  - **Depends on**: W1.1

- [ ] **W3.2**: Build Kanban board layout
  - **Type**: feature
  - **Status**: TODO
  - **Description**: 3 columns (TODO, IN_PROGRESS, DONE), animated column cards, drag overlay with Framer Motion
  - **Acceptance**: Kanban board renders, columns animate
  - **Depends on**: W3.1

- [ ] **W3.3**: Implement drag-drop logic with API updates
  - **Type**: feature
  - **Status**: TODO
  - **Description**: Move tasks between columns, POST to update status, optimistic updates, smooth reordering
  - **Acceptance**: Drag-drop works, API updates, animations are smooth (60fps)
  - **Depends on**: W3.2, W2.1

- [ ] **W3.4**: Create animated task card component
  - **Type**: feature
  - **Status**: TODO
  - **Description**: Task card with hover effects, click to expand modal, show details/dependencies/labels
  - **Acceptance**: Cards look beautiful, modal animations work
  - **Depends on**: W3.2

### Phase 4: Real-Time Updates
**Goal**: WebSocket for live task/signal updates across users

- [ ] **W4.1**: Create WebSocket endpoint in FastAPI
  - **Type**: feature
  - **Status**: TODO
  - **Description**: `/ws/sessions/:id` endpoint, broadcast task/signal changes, connection management
  - **Acceptance**: WebSocket connects, receives test messages
  - **Depends on**: W2.1

- [ ] **W4.2**: Build useWebSocket React hook
  - **Type**: feature
  - **Status**: TODO
  - **Description**: Auto-reconnect, message type handling, error handling, connection status indicator
  - **Acceptance**: Hook connects, reconnects on disconnect, handles errors gracefully
  - **Depends on**: W4.1

- [ ] **W4.3**: Integrate real-time task updates in Kanban
  - **Type**: feature
  - **Status**: TODO
  - **Description**: Subscribe to task changes, animate task moves from other users, show who's working on what
  - **Acceptance**: Tasks update live across browser tabs, smooth animations
  - **Depends on**: W4.2, W3.3

- [ ] **W4.4**: Integrate real-time signal updates
  - **Type**: feature
  - **Status**: TODO
  - **Description**: Live signal badge updates, alert animations, system notifications
  - **Acceptance**: Signals update live, animations fire on changes
  - **Depends on**: W4.2, W2.4

### Phase 5: Observability Dashboard
**Goal**: Visualize logs, traces, errors, LLM calls

- [ ] **W5.1**: Create observability API endpoints
  - **Type**: feature
  - **Status**: TODO
  - **Description**:
    ```
    GET /api/sessions/:id/logs - JSONL logs
    GET /api/sessions/:id/traces - Trace data
    GET /api/sessions/:id/errors - Error context
    GET /api/sessions/:id/llm-calls - LLM history
    ```
  - **Acceptance**: All endpoints return correct data from dev_mode/
  - **Depends on**: W2.1

- [ ] **W5.2**: Build logs viewer with search/filter
  - **Type**: feature
  - **Status**: TODO
  - **Description**: Display JSONL logs, syntax highlighting, search, real-time streaming
  - **Acceptance**: Can view and search logs easily
  - **Depends on**: W5.1

- [ ] **W5.3**: Build traces visualization
  - **Type**: feature
  - **Status**: TODO
  - **Description**: Trace timeline, span breakdown, waterfall chart, performance metrics
  - **Acceptance**: Can see trace data visually, identify bottlenecks
  - **Depends on**: W5.1

- [ ] **W5.4**: Build errors dashboard
  - **Type**: feature
  - **Status**: TODO
  - **Description**: Error list, stack traces, error context, group by trace_id, error rate chart
  - **Acceptance**: Can debug errors effectively with full context
  - **Depends on**: W5.1

### Phase 6: Polish & Production
**Goal**: Performance, accessibility, deployment ready

- [ ] **W6.1**: Performance optimization
  - **Type**: chore
  - **Status**: TODO
  - **Description**: Code splitting, lazy loading, image optimization, bundle analysis, <500KB initial load
  - **Acceptance**: Lighthouse score 90+ on all metrics
  - **Depends on**: All W1-W5

- [ ] **W6.2**: Accessibility improvements
  - **Type**: chore
  - **Status**: TODO
  - **Description**: ARIA labels, keyboard navigation, screen reader testing, WCAG AA compliance
  - **Acceptance**: Screen reader works, keyboard nav works, color contrast passes
  - **Depends on**: All W1-W5

- [ ] **W6.3**: Animation polish pass
  - **Type**: chore
  - **Status**: TODO
  - **Description**: Smooth all transitions, add loading skeletons, microinteractions, gesture support
  - **Acceptance**: 60fps everywhere, no jank, feels polished
  - **Depends on**: All W1-W5

- [ ] **W6.4**: Production deployment setup
  - **Type**: chore
  - **Status**: TODO
  - **Description**: Docker setup, environment config, build optimization, monitoring
  - **Acceptance**: Can deploy to production, monitoring works
  - **Depends on**: All W1-W5

---

## 🎨 Design System

### Colors
- **Primary**: Blue (#3b82f6)
- **Success**: Green (#10b981)
- **Warning**: Yellow (#f59e0b)
- **Error**: Red (#ef4444)
- **Task States**:
  - TODO: Gray (#6b7280)
  - IN_PROGRESS: Blue (#3b82f6)
  - DONE: Green (#10b981)

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

See also:
- **Research**: `/tmp/website-plan-research.md` (full tech evaluation)
- **Main Plan**: `docs/plan.md` (extracted P5.1, P5.2 moved here)
- **Architecture**: `docs/architecture.md` (backend integration points)

---

## 🔄 Development Workflow

### Setup (One-time)
```bash
# 1. Create frontend project
cd /Users/honk/code/planloop
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install

# 2. Install dependencies
npm install -D tailwindcss postcss autoprefixer
npm install framer-motion react-router-dom @dnd-kit/core @dnd-kit/sortable

# 3. Configure Tailwind
npx tailwindcss init -p
```

### Daily Development
```bash
# Terminal 1: Frontend dev server (with HMR)
cd frontend && npm run dev

# Terminal 2: Backend server
cd /Users/honk/code/planloop
source .venv/bin/activate
planloop web
```

### Build & Deploy
```bash
# Build frontend
cd frontend && npm run build

# FastAPI serves frontend/dist/ automatically
planloop web --host 0.0.0.0 --port 8000
```

---

## ✅ Success Metrics

- [ ] **Performance**: Lighthouse 90+ (all categories)
- [ ] **Accessibility**: WCAG AA compliance
- [ ] **Animation**: 60fps, no jank
- [ ] **Bundle**: <500KB initial load
- [ ] **Real-time**: <100ms WebSocket latency
- [ ] **Mobile**: Fully responsive

---

## 🚀 Next Steps

1. ✅ Research complete (quality score: 9/10)
2. ✅ Plan created (this file)
3. ⏭️ Start W1.1: Initialize Vite project
4. ⏭️ Follow TDD for all components (write tests first!)

---

*For implementation details, animation specs, and code examples, see `/tmp/website-plan-research.md`*
