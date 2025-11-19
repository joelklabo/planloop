# Task Management Web UI - Testing Strategy

**Status**: In Progress  
**Author**: AI Agent  
**Created**: 2025-11-18  
**Session**: task-management-ui-20251118T232926Z-c261

## Overview

Comprehensive testing strategy for the task management web UI, covering unit tests, component tests, integration tests, and end-to-end tests.

## Testing Pyramid

```
       ┌─────────────┐
       │   E2E (5%)  │  Playwright - Critical user journeys
       ├─────────────┤
       │ Integration │  React Testing Library - Component integration
       │    (15%)    │
       ├─────────────┤
       │   Unit      │  Vitest - Functions, utilities, hooks
       │   (80%)     │
       └─────────────┘
```

## Technology Stack

### Unit & Component Testing
- **Vitest**: Fast unit test runner (Vite-native)
- **React Testing Library**: Component testing
- **MSW (Mock Service Worker)**: API mocking
- **@testing-library/user-event**: User interaction simulation

### E2E Testing
- **Playwright**: Cross-browser E2E testing
- **@playwright/test**: Test runner
- Target: Chrome, Firefox, Safari

## Test Coverage Goals

- **Overall**: 80%+ coverage
- **Critical paths**: 100% coverage (auth, CRUD operations)
- **UI components**: 70%+ coverage
- **Utility functions**: 90%+ coverage
- **API clients**: 100% coverage

## Testing Layers

### Layer 1: Unit Tests (80% of tests)

**What to test**:
- Pure functions
- Utility functions
- Custom hooks (without component rendering)
- Type guards and validators
- Business logic

**Example structure**:
```
tests/
├── unit/
│   ├── utils/
│   │   ├── date-formatting.test.ts
│   │   ├── task-filtering.test.ts
│   │   └── validation.test.ts
│   ├── hooks/
│   │   ├── useTasks.test.ts
│   │   ├── useTaskSearch.test.ts
│   │   └── useTaskMutations.test.ts
│   └── api/
│       └── tasks.test.ts
```

**Key tests**:
- ✅ Date formatting (formatDate function)
- ✅ Task filtering logic
- ✅ Form validation
- ✅ API client functions
- ✅ Custom hooks with mocked dependencies

### Layer 2: Component Tests (15% of tests)

**What to test**:
- Component rendering
- User interactions
- State changes
- Conditional rendering
- Accessibility

**Example structure**:
```
tests/
├── components/
│   ├── ui/
│   │   ├── Toast.test.tsx
│   │   ├── ConfirmDialog.test.tsx
│   │   └── Button.test.tsx
│   └── tasks/
│       ├── TaskToolbar.test.tsx
│       ├── TaskDetailPanel.test.tsx
│       └── TasksPage.test.tsx
```

**Key tests**:
- ✅ TaskToolbar: Search, filters, interactions
- ✅ TaskDetailPanel: Form submission, validation
- ✅ TasksPage: Table rendering, sorting, pagination
- ✅ Toast: Display, auto-dismiss, close
- ✅ ConfirmDialog: Show/hide, confirm/cancel

### Layer 3: Integration Tests (5% of tests)

**What to test**:
- Component integration with React Query
- API integration with MSW
- Router integration
- Full user flows (without browser)

**Example structure**:
```
tests/
├── integration/
│   ├── task-crud-flow.test.tsx
│   ├── search-and-filter.test.tsx
│   └── pagination.test.tsx
```

**Key tests**:
- ✅ Create task flow
- ✅ Edit task flow
- ✅ Delete task flow
- ✅ Search with results
- ✅ Filter combination
- ✅ Pagination navigation

### Layer 4: E2E Tests (5% of tests)

**What to test**:
- Critical user journeys
- Cross-browser compatibility
- Real API integration
- Visual regression (optional)

**Example structure**:
```
e2e/
├── fixtures/
│   └── test-data.ts
├── pages/
│   └── tasks-page.ts (Page Object Model)
└── specs/
    ├── task-management.spec.ts
    ├── search-filter.spec.ts
    └── responsive.spec.ts
```

**Key tests**:
- ✅ Complete task creation journey
- ✅ Complete task edit journey
- ✅ Search → Select → Edit → Save
- ✅ Multi-filter application
- ✅ Pagination through results
- ✅ Delete with confirmation
- ✅ Mobile responsive behavior

## Implementation Plan

### Phase 1: Setup Testing Infrastructure (Task 36)

**Estimated**: 1 hour

1. Install dependencies:
```bash
npm install -D vitest @vitest/ui @vitest/coverage-v8
npm install -D @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm install -D msw
npm install -D @playwright/test
```

2. Configure Vitest (`vitest.config.ts`)
3. Configure Playwright (`playwright.config.ts`)
4. Add test scripts to package.json
5. Create test utilities and setup files

**Success criteria**:
- ✅ `npm test` runs Vitest
- ✅ `npm run test:e2e` runs Playwright
- ✅ `npm run test:coverage` shows coverage report
- ✅ Tests can import components without errors

### Phase 2: Unit Tests (Tasks 37-39)

**Task 37: API Client Tests** (30 min)
- Test `tasksApi.getTasks` with various params
- Test `tasksApi.createTask`
- Test `tasksApi.updateTask`
- Test `tasksApi.deleteTask`
- Test error handling

**Task 38: Hook Tests** (45 min)
- Test `useTasks` with React Query
- Test `useTaskSearch` with debouncing
- Test `useCreateTask` mutation
- Test `useUpdateTask` mutation
- Test `useDeleteTask` mutation

**Task 39: Utility Tests** (30 min)
- Test `formatDate` function
- Test status badge color logic
- Test type badge icon logic
- Test pagination calculations

### Phase 3: Component Tests (Tasks 40-43)

**Task 40: UI Component Tests** (1 hour)
- Toast: Render, auto-dismiss, close button
- ConfirmDialog: Show/hide, actions
- Test accessibility (aria labels, keyboard nav)

**Task 41: TaskToolbar Tests** (1 hour)
- Search input changes
- Autocomplete dropdown
- Keyboard navigation (↑↓ Enter Esc)
- Filter dropdowns
- Clear filters button
- New task button click

**Task 42: TasksPage Tests** (1.5 hours)
- Table renders tasks correctly
- Column sorting works
- Pagination controls
- Row click opens panel
- Delete button shows confirmation
- Empty state displays
- Loading state displays
- Error state displays

**Task 43: TaskDetailPanel Tests** (1 hour)
- Renders for new task
- Renders for existing task
- Form fields populated
- Form validation
- Submit button
- Close button
- Escape key closes

### Phase 4: Integration Tests (Tasks 44-45)

**Task 44: CRUD Flow Tests** (1.5 hours)
- Create task → appears in list
- Edit task → updates in list
- Delete task → removes from list
- Search filters results
- Filters combine correctly

**Task 45: React Query Integration** (1 hour)
- Cache updates on mutation
- Optimistic updates work
- Error handling displays toast
- Retry logic works

### Phase 5: E2E Tests (Tasks 46-48)

**Task 46: Setup Page Objects** (30 min)
- Create TasksPage page object
- Create reusable selectors
- Create helper functions

**Task 47: Critical Path E2E Tests** (2 hours)
- Full task creation flow
- Full task edit flow
- Full task deletion flow
- Search and filter flow

**Task 48: Cross-Browser & Responsive** (1 hour)
- Run on Chrome, Firefox, Safari
- Test mobile viewport
- Test tablet viewport
- Visual regression tests (optional)

## Test Execution

### Local Development

```bash
# Run all unit/component tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run E2E in headed mode (see browser)
npm run test:e2e -- --headed

# Run specific E2E test
npm run test:e2e -- task-management.spec.ts
```

### CI/CD Integration

**GitHub Actions workflow**:
```yaml
- name: Run unit tests
  run: npm test -- --run

- name: Run E2E tests
  run: npm run test:e2e

- name: Upload coverage
  run: npm run test:coverage
```

## Mocking Strategy

### API Mocking with MSW

**Setup**:
```typescript
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('/api/tasks', ({ request }) => {
    const url = new URL(request.url)
    const search = url.searchParams.get('search')
    // Return mock data
    return HttpResponse.json({
      tasks: mockTasks,
      total: 100,
      page: 1,
      pageSize: 50,
    })
  }),
]
```

**Use in tests**:
```typescript
import { setupServer } from 'msw/node'
import { handlers } from '@/mocks/handlers'

const server = setupServer(...handlers)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

### Test Data Management

**Fixtures**:
```typescript
// tests/fixtures/tasks.ts
export const mockTask = {
  id: 1,
  title: 'Test task',
  session: 'test-session',
  session_name: 'Test Session',
  status: 'TODO',
  type: 'feature',
  // ...
}

export const mockTasks = [mockTask, ...]
```

## Accessibility Testing

**Key checks**:
- ✅ Keyboard navigation works
- ✅ Screen reader support (aria-labels)
- ✅ Focus management (modals, panels)
- ✅ Color contrast meets WCAG AA
- ✅ Form labels associated
- ✅ Error messages announced

**Tools**:
- `@axe-core/playwright` for automated a11y tests
- Manual keyboard testing
- Screen reader testing (VoiceOver, NVDA)

## Performance Testing

**Metrics to track**:
- Initial load time
- Time to interactive
- Component render time
- List virtualization performance
- Bundle size

**Tools**:
- Lighthouse CI
- Playwright performance traces
- React DevTools Profiler

## Coverage Reports

**Generate**:
```bash
npm run test:coverage
```

**View**:
- Terminal summary
- HTML report: `coverage/index.html`
- Upload to Codecov (CI)

**Coverage thresholds** (enforced in vitest.config.ts):
```typescript
coverage: {
  statements: 80,
  branches: 75,
  functions: 80,
  lines: 80,
}
```

## Common Testing Patterns

### Testing Async Behavior

```typescript
import { waitFor, screen } from '@testing-library/react'

test('loads and displays tasks', async () => {
  render(<TasksPage />)
  
  await waitFor(() => {
    expect(screen.getByText('Task 1')).toBeInTheDocument()
  })
})
```

### Testing User Interactions

```typescript
import userEvent from '@testing-library/user-event'

test('opens detail panel on task click', async () => {
  const user = userEvent.setup()
  render(<TasksPage />)
  
  await user.click(screen.getByText('Task 1'))
  
  expect(screen.getByRole('dialog')).toBeInTheDocument()
})
```

### Testing Forms

```typescript
test('validates required fields', async () => {
  const user = userEvent.setup()
  render(<TaskForm />)
  
  await user.click(screen.getByRole('button', { name: /save/i }))
  
  expect(screen.getByText(/title is required/i)).toBeInTheDocument()
})
```

### Testing React Query

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}
```

## Debugging Tests

**Vitest**:
```bash
# Run in UI mode
npm test -- --ui

# Debug specific test
npm test -- task-toolbar.test.ts --reporter=verbose
```

**Playwright**:
```bash
# Debug mode (pauses on failures)
npm run test:e2e -- --debug

# Show trace viewer
npx playwright show-trace trace.zip
```

## Success Metrics

**Phase completion criteria**:
- ✅ All tests passing
- ✅ 80%+ overall coverage
- ✅ 100% coverage on critical paths
- ✅ E2E tests pass on 3 browsers
- ✅ No accessibility violations
- ✅ CI pipeline green

**Quality gates**:
- No test with >5 second runtime (except E2E)
- No flaky tests (must pass 10 runs)
- All tests have descriptive names
- All tests follow AAA pattern (Arrange, Act, Assert)

## Timeline

**Total estimated effort**: 12-15 hours

- Phase 1 (Setup): 1 hour
- Phase 2 (Unit): 2 hours
- Phase 3 (Component): 4.5 hours
- Phase 4 (Integration): 2.5 hours
- Phase 5 (E2E): 3.5 hours

**Target completion**: By end of Task 48

## Next Steps

1. ✅ Create this testing strategy document
2. ⏭️ Implement Phase 1: Setup infrastructure (Task 36)
3. ⏭️ Begin systematic test implementation following TDD
4. ⏭️ Monitor coverage and quality metrics
5. ⏭️ Update agents.md with testing patterns learned

---

**Note**: This strategy may evolve as we discover new requirements or challenges. All changes will be documented here.
