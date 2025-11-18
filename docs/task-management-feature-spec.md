# Task Management Feature - Comprehensive Specification

**Version**: 1.0  
**Date**: 2025-11-18  
**Status**: Ready for Implementation

---

## Executive Summary

This specification defines a comprehensive task management interface for the planloop website that allows users to view, search, filter, sort, create, edit, move, and delete tasks across sessions. The interface emphasizes modern UX principles, smooth animations, accessibility, and a delightful user experience.

### Key Features
- ✅ Comprehensive task list view with powerful filtering and search
- ✅ Smooth animations for all state transitions
- ✅ Side panel detail view for task editing
- ✅ Drag-and-drop to move tasks between sessions
- ✅ Autocomplete search with instant results
- ✅ Responsive design (mobile to desktop)
- ✅ Full accessibility (WCAG 2.1 AA compliant)
- ✅ Keyboard navigation support
- ✅ Consistent with existing session management patterns

---

## Design Principles (2025 Best Practices)

### 1. User-Centered Design
- Deep understanding of task management workflows
- Iterative feedback loops
- Minimize cognitive load at every interaction

### 2. Minimalism & Clarity
- Clean, uncluttered interface
- Ample white space
- Clear visual hierarchy
- Focus on essential actions

### 3. Consistency
- Reuse session management components where possible
- Consistent visual language (colors, icons, buttons)
- Predictable interaction patterns

### 4. Micro-Interactions
- Immediate visual feedback for all actions
- Smooth transitions using Framer Motion
- Delight without distraction

### 5. Accessibility First
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader support
- High contrast modes
- Respect prefers-reduced-motion

### 6. Performance
- Virtualized rendering for large task lists (1000+ tasks)
- Optimistic UI updates
- Debounced search/filter
- Memoization to prevent unnecessary re-renders

---

## User Flows

### Primary Flow: View & Search Tasks
```
1. User navigates to /tasks page
2. System displays all tasks across all sessions (paginated)
3. User sees search bar with autocomplete
4. User types query → autocomplete suggests matches
5. Results filter instantly as user types
6. User can apply additional filters (session, status, type)
7. User clicks task → side panel opens with details
```

### Secondary Flow: Edit Task
```
1. User clicks task in list
2. Side panel slides in from right with task details
3. User edits fields (title, status, type, notes)
4. Changes auto-save (or manual save button)
5. Success toast notification
6. Side panel updates, list reflects changes
7. User clicks outside or close button → panel closes smoothly
```

### Tertiary Flow: Move Task Between Sessions
```
1. User drags task from list
2. Visual feedback (ghost preview, drop zones highlight)
3. User drops on different session indicator
4. Confirmation modal "Move task to [Session X]?"
5. User confirms
6. API call with optimistic UI update
7. Task animates to new position
8. Success notification
```

### Quaternary Flow: Create New Task
```
1. User clicks "New Task" button (floating or toolbar)
2. Side panel opens with empty form
3. User fills in required fields (title, session)
4. Optional fields (type, status, notes, dependencies)
5. User clicks "Create"
6. API call with optimistic UI
7. New task appears in list with animation
8. Success notification
```

### Quinary Flow: Delete Task
```
1. User clicks delete icon on task (or in detail panel)
2. Confirmation modal appears
3. User confirms
4. Optimistic UI removal with exit animation
5. API call
6. Success notification with undo option
```

---

## Component Architecture

### High-Level Component Tree
```
<TaskManagementPage>
  ├── <TaskToolbar>
  │   ├── <SearchBar> (with autocomplete)
  │   ├── <FilterDropdowns> (session, status, type)
  │   ├── <ViewToggle> (table/kanban)
  │   └── <NewTaskButton>
  │
  ├── <TaskListView>
  │   ├── <VirtualizedTable> (TanStack Table)
  │   │   ├── <TaskRow> (multiple, memoized)
  │   │   │   ├── <TaskCell> (title, status, session, etc.)
  │   │   │   └── <TaskActions> (edit, delete icons)
  │   │   └── <EmptyState> (when no tasks)
  │   └── <Pagination>
  │
  ├── <TaskDetailPanel>
  │   ├── <PanelHeader> (title, close button)
  │   ├── <TaskForm>
  │   │   ├── <TextField> (title)
  │   │   ├── <Select> (session, status, type)
  │   │   ├── <TextArea> (implementation notes)
  │   │   ├── <DependencyPicker>
  │   │   └── <FormActions> (save, cancel)
  │   └── <TaskMetadata> (created, updated, commit_sha)
  │
  ├── <ConfirmationModal>
  │   ├── <ModalHeader>
  │   ├── <ModalBody>
  │   └── <ModalActions> (confirm, cancel)
  │
  └── <ToastNotifications>
      └── <Toast> (multiple, animated)
```

### Component Reusability

**Reuse from Session Management:**
- `<SearchBar>` with autocomplete
- `<FilterDropdowns>`
- `<Pagination>`
- `<ToastNotifications>`
- `<ConfirmationModal>`

**New Task-Specific Components:**
- `<TaskListView>`
- `<TaskRow>`
- `<TaskDetailPanel>`
- `<TaskForm>`
- `<TaskActions>`

---

## Detailed Component Specifications

### 1. TaskManagementPage

**Purpose**: Main container for task management interface

**State**:
```typescript
interface TaskManagementState {
  tasks: Task[];
  filteredTasks: Task[];
  selectedTask: Task | null;
  isPanelOpen: boolean;
  searchQuery: string;
  filters: {
    session: string | null;
    status: TaskStatus[];
    type: TaskType[];
  };
  sort: {
    column: string;
    direction: 'asc' | 'desc';
  };
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
  isLoading: boolean;
  error: string | null;
}
```

**API Integration**:
```typescript
// GET /api/tasks?page=1&pageSize=50&search=query&session=id&status=TODO,IN_PROGRESS
// POST /api/tasks - create task
// PUT /api/tasks/:id - update task
// DELETE /api/tasks/:id - delete task
// POST /api/tasks/:id/move - move task to different session
```

**Hooks**:
```typescript
const {
  tasks,
  isLoading,
  error,
  searchTasks,
  filterTasks,
  sortTasks,
  createTask,
  updateTask,
  deleteTask,
  moveTask,
} = useTasks();

const {
  isPanelOpen,
  selectedTask,
  openPanel,
  closePanel,
} = useTaskPanel();
```

---

### 2. TaskToolbar

**Purpose**: Search, filter, and action bar

**Props**:
```typescript
interface TaskToolbarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  filters: Filters;
  onFilterChange: (filters: Filters) => void;
  onNewTask: () => void;
  totalTasks: number;
  filteredCount: number;
}
```

**Features**:
- **Search Bar**: Autocomplete with task title suggestions
- **Filter Dropdowns**: Session (multi-select), Status (multi-select), Type (multi-select)
- **New Task Button**: Floating action button (FAB) or toolbar button
- **Results Counter**: "Showing 15 of 234 tasks"
- **Clear Filters**: Quick button to reset all filters

**Autocomplete Behavior**:
- Debounce input (300ms)
- Show top 10 matches
- Highlight matching text
- Keyboard navigation (up/down arrows, enter to select)
- Click outside to close
- Show "No results" message when empty

**Visual Design**:
```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 Search tasks...            │ Session ▾ │ Status ▾ │ Type ▾ │ + New Task │
│                                │           │          │        │            │
│ Showing 15 of 234 tasks                               Clear Filters        │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3. TaskListView (TanStack Table)

**Purpose**: Main task list with sorting, filtering, pagination

**Technology**: TanStack Table v8 (headless, flexible, performant)

**Columns**:
```typescript
const columns = [
  { id: 'id', header: 'ID', accessorKey: 'id', size: 60 },
  { id: 'title', header: 'Title', accessorKey: 'title', size: 300 },
  { id: 'session', header: 'Session', accessorKey: 'session_name', size: 150 },
  { id: 'status', header: 'Status', accessorKey: 'status', size: 120 },
  { id: 'type', header: 'Type', accessorKey: 'type', size: 100 },
  { id: 'updated', header: 'Last Updated', accessorKey: 'last_updated_at', size: 150 },
  { id: 'actions', header: '', cell: TaskActionsCell, size: 80 },
];
```

**Features**:
- **Column Sorting**: Click header to sort (asc/desc), visual indicator (↑↓)
- **Row Selection**: Checkbox for bulk actions (future feature)
- **Row Click**: Opens detail panel
- **Row Hover**: Highlight with subtle background change
- **Empty State**: "No tasks found. Create your first task!" with illustration
- **Loading State**: Skeleton rows while fetching
- **Error State**: Error message with retry button

**Performance**:
- Virtualization for 1000+ rows (react-window or native TanStack virtualization)
- Memoized row components
- Debounced search/filter updates

**Responsive Design**:
- Desktop: Full table with all columns
- Tablet: Hide 'Type' and 'Updated' columns
- Mobile: Card view instead of table (future enhancement)

---

### 4. TaskDetailPanel (Side Panel)

**Purpose**: View and edit task details

**Behavior**:
- Slides in from right side (300ms animation)
- Overlays main content with semi-transparent backdrop
- Click outside or ESC key to close
- Smooth slide-out animation on close
- Auto-save mode (debounced) or manual save button

**Layout**:
```
┌────────────────────────────────────┐
│  Edit Task                    ✕    │ ← Header (sticky)
├────────────────────────────────────┤
│                                    │
│  Title *                           │
│  ┌──────────────────────────────┐ │
│  │ [Task title input]           │ │
│  └──────────────────────────────┘ │
│                                    │
│  Session *                         │
│  ┌──────────────────────────────┐ │
│  │ [Session dropdown]      ▾    │ │
│  └──────────────────────────────┘ │
│                                    │
│  Status                            │
│  ┌──────────────────────────────┐ │
│  │ [Status dropdown]       ▾    │ │
│  └──────────────────────────────┘ │
│                                    │
│  Type                              │
│  ┌──────────────────────────────┐ │
│  │ [Type dropdown]         ▾    │ │
│  └──────────────────────────────┘ │
│                                    │
│  Implementation Notes              │
│  ┌──────────────────────────────┐ │
│  │ [Textarea]                   │ │
│  │                              │ │
│  │                              │ │
│  └──────────────────────────────┘ │
│                                    │
│  Dependencies (Optional)           │
│  ┌──────────────────────────────┐ │
│  │ [Multi-select of task IDs]  │ │
│  └──────────────────────────────┘ │
│                                    │
│  ─────────────────────────────── │
│  Created: 2025-11-18 10:00 AM     │
│  Updated: 2025-11-18 11:30 AM     │
│  Commit: abc1234                  │
│                                    │
├────────────────────────────────────┤
│  [Save Changes]  [Cancel] [Delete]│ ← Footer (sticky)
└────────────────────────────────────┘
```

**Form Validation**:
- Title: Required, min 3 characters, max 200 characters
- Session: Required, must be valid session ID
- Status: Required, must be valid TaskStatus enum
- Type: Optional, must be valid TaskType enum
- Implementation Notes: Optional, max 5000 characters
- Dependencies: Optional, task IDs must exist and not create circular dependencies

**API Calls**:
- Auto-save: Debounced PUT request after 1 second of inactivity
- Manual save: Immediate PUT request
- Validation errors show inline below fields
- Success toast on save
- Error toast on failure with retry option

**Animations**:
```typescript
// Panel entrance
<motion.div
  initial={{ x: '100%' }}
  animate={{ x: 0 }}
  exit={{ x: '100%' }}
  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
>
```

---

### 5. SearchBar with Autocomplete

**Purpose**: Fast task search with intelligent suggestions

**Features**:
- **Instant Search**: Debounced (300ms) API call
- **Autocomplete Dropdown**: Top 10 matches as user types
- **Highlight Matches**: Bold the matching text
- **Keyboard Navigation**: 
  - Arrow keys (up/down) to navigate suggestions
  - Enter to select
  - Escape to close dropdown
  - Tab to select and move to next field
- **Click Outside**: Close dropdown
- **Show Session Context**: "Task 123: Fix bug in parser (Session: v17-dev)"
- **Show Match Count**: "15 results for 'auth'"

**Matching Logic**:
- Search across: title, implementation_notes, session_name
- Fuzzy matching (tolerate typos)
- Ranking: exact match > starts with > contains > fuzzy

**Visual States**:
- Default: "Search tasks..."
- Focus: Border highlight, dropdown opens
- Typing: Show loading spinner in input
- Results: Dropdown with suggestions
- No results: "No tasks match 'xyz'"
- Error: "Search unavailable. Try again."

**Component**:
```typescript
interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSelect: (task: Task) => void;
  placeholder?: string;
  disabled?: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({ ... }) => {
  const [suggestions, setSuggestions] = useState<Task[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  
  // Debounced search
  const debouncedSearch = useDebouncedCallback((query) => {
    fetchSuggestions(query).then(setSuggestions);
  }, 300);
  
  // Keyboard handler
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'ArrowDown') { /* navigate down */ }
    if (e.key === 'ArrowUp') { /* navigate up */ }
    if (e.key === 'Enter') { /* select active */ }
    if (e.key === 'Escape') { /* close */ }
  };
  
  return (
    <div className="search-bar-container">
      <input
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          debouncedSearch(e.target.value);
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
      />
      {isOpen && suggestions.length > 0 && (
        <AutocompleteDropdown
          suggestions={suggestions}
          activeIndex={activeIndex}
          onSelect={onSelect}
        />
      )}
    </div>
  );
};
```

---

### 6. Filter Dropdowns

**Purpose**: Multi-select filters for session, status, type

**Component**: Custom multi-select dropdown (or Headless UI Listbox)

**Features**:
- **Session Filter**: Multi-select with checkboxes
  - Show session name and count: "v17-dev (23 tasks)"
  - "All Sessions" option to clear filter
  - Search within sessions (if 10+ sessions)
  
- **Status Filter**: Multi-select with checkboxes
  - TODO, IN_PROGRESS, DONE, BLOCKED, etc.
  - Color-coded badges
  - "Select All" / "Clear All" options
  
- **Type Filter**: Multi-select with checkboxes
  - feature, fix, test, chore, etc.
  - Icon indicators
  - "Select All" / "Clear All" options

**Visual Design**:
```
┌────────────────────────┐
│ Session ▾              │
├────────────────────────┤
│ ☑ All Sessions         │
│ ☐ v17-dev (23)         │
│ ☐ v16-fixes (12)       │
│ ☐ v15-stable (8)       │
│ ─────────────────────  │
│ [Apply] [Clear]        │
└────────────────────────┘
```

**State Management**:
```typescript
const [sessionFilter, setSessionFilter] = useState<string[]>([]);
const [statusFilter, setStatusFilter] = useState<TaskStatus[]>([]);
const [typeFilter, setTypeFilter] = useState<TaskType[]>([]);

// Apply filters
const filteredTasks = tasks.filter(task => {
  const matchesSession = sessionFilter.length === 0 || sessionFilter.includes(task.session);
  const matchesStatus = statusFilter.length === 0 || statusFilter.includes(task.status);
  const matchesType = typeFilter.length === 0 || typeFilter.includes(task.type);
  return matchesSession && matchesStatus && matchesType;
});
```

---

### 7. Pagination Component

**Purpose**: Navigate through large task lists

**Props**:
```typescript
interface PaginationProps {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}
```

**Features**:
- Page size selector: 25, 50, 100, 200
- Page navigation: Previous, Next, First, Last
- Current page indicator: "Page 3 of 12"
- Direct page jump: Input field to jump to page
- Showing range: "Showing 51-100 of 234"
- Disabled states when on first/last page

**Visual Design**:
```
┌─────────────────────────────────────────────────────────────────┐
│ Rows per page: [50 ▾]    ◀◀  ◀  Page 3 of 12  ▶  ▶▶            │
│                           Showing 51-100 of 234 tasks            │
└─────────────────────────────────────────────────────────────────┘
```

---

### 8. Drag and Drop (Move Task Between Sessions)

**Technology**: React DnD or react-beautiful-dnd (or native if simple)

**Behavior**:
1. User hovers over task row → Drag handle appears (⋮⋮)
2. User drags task → Ghost preview follows cursor
3. Drop zones highlight (other sessions in sidebar?)
4. User drops on session → Confirmation modal
5. User confirms → API call + optimistic UI
6. Task animates to new position or disappears with "Moved to [Session]" toast

**Visual Feedback**:
- Ghost preview with semi-transparent task card
- Drop zones highlight with border + background color
- Cursor changes to indicate droppable/not-droppable

**Accessibility**:
- Keyboard support: Select task, press "M", choose session from modal
- Screen reader announcements: "Task dragged", "Drop zone available", "Task moved"

**Confirmation Modal**:
```
┌────────────────────────────────────────┐
│  Move Task to Different Session?       │
├────────────────────────────────────────┤
│                                        │
│  Task: "Fix auth bug in parser"        │
│  From: v17-development                 │
│  To:   v16-fixes                       │
│                                        │
│  This will update the task's session   │
│  assignment. Continue?                 │
│                                        │
├────────────────────────────────────────┤
│        [Cancel]  [Move Task]           │
└────────────────────────────────────────┘
```

---

### 9. Animations & Transitions (Framer Motion)

**Philosophy**: Smooth, purposeful, accessible

**Key Animations**:

**1. Panel Slide-In/Out**:
```typescript
<motion.div
  initial={{ x: '100%', opacity: 0 }}
  animate={{ x: 0, opacity: 1 }}
  exit={{ x: '100%', opacity: 0 }}
  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
>
  <TaskDetailPanel />
</motion.div>
```

**2. Task List Entrance (Staggered)**:
```typescript
<AnimatePresence>
  {tasks.map((task, index) => (
    <motion.tr
      key={task.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <TaskRow task={task} />
    </motion.tr>
  ))}
</AnimatePresence>
```

**3. Toast Notifications**:
```typescript
<motion.div
  initial={{ opacity: 0, y: -50, scale: 0.3 }}
  animate={{ opacity: 1, y: 0, scale: 1 }}
  exit={{ opacity: 0, scale: 0.5, transition: { duration: 0.2 } }}
  transition={{ type: 'spring', stiffness: 300, damping: 20 }}
>
  <Toast message={message} type={type} />
</motion.div>
```

**4. Drag Preview**:
```typescript
<motion.div
  drag
  dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
  dragElastic={0.1}
  whileDrag={{ scale: 1.05, opacity: 0.8 }}
>
  <TaskCard task={task} />
</motion.div>
```

**5. Filter Badge Appear**:
```typescript
<motion.span
  initial={{ scale: 0 }}
  animate={{ scale: 1 }}
  exit={{ scale: 0 }}
  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
>
  Active Filter Badge
</motion.span>
```

**Accessibility**:
- Respect `prefers-reduced-motion` media query
- Disable animations if user has motion sensitivity
- Fallback to instant transitions

```typescript
const prefersReducedMotion = useReducedMotion();

const transition = prefersReducedMotion 
  ? { duration: 0 } 
  : { type: 'spring', stiffness: 300, damping: 30 };
```

---

### 10. Toast Notifications

**Purpose**: Non-intrusive feedback for actions

**Types**:
- **Success**: Green checkmark icon, "Task created successfully"
- **Error**: Red X icon, "Failed to delete task. Try again."
- **Info**: Blue info icon, "Task moved to v16-fixes"
- **Warning**: Yellow warning icon, "Unsaved changes will be lost"

**Behavior**:
- Appear at top-right corner
- Auto-dismiss after 4 seconds (configurable)
- Manual dismiss with X button
- Stack multiple toasts vertically
- Animate in/out with Framer Motion
- Action button for undo (when applicable)

**Component**:
```typescript
interface ToastProps {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  duration?: number;
  onDismiss: (id: string) => void;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const Toast: React.FC<ToastProps> = ({ ... }) => {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(id), duration || 4000);
    return () => clearTimeout(timer);
  }, []);
  
  return (
    <motion.div
      className={`toast toast-${type}`}
      initial={{ opacity: 0, y: -50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.5 }}
    >
      <Icon type={type} />
      <span>{message}</span>
      {action && <button onClick={action.onClick}>{action.label}</button>}
      <button onClick={() => onDismiss(id)}>✕</button>
    </motion.div>
  );
};
```

---

## Data Types & API Contracts

### Task Type
```typescript
interface Task {
  id: number;
  title: string;
  session: string;               // Session ID
  session_name: string;          // Denormalized for display
  type: TaskType;
  status: TaskStatus;
  depends_on: number[];
  implementation_notes: string | null;
  commit_sha: string | null;
  created_at: string;            // ISO 8601
  last_updated_at: string | null; // ISO 8601
}

type TaskType = 
  | 'feature'
  | 'fix'
  | 'test'
  | 'chore'
  | 'refactor'
  | 'doc'
  | 'design'
  | 'investigate';

type TaskStatus =
  | 'TODO'
  | 'IN_PROGRESS'
  | 'DONE'
  | 'BLOCKED'
  | 'CANCELLED'
  | 'SKIPPED'
  | 'OUT_OF_SCOPE'
  | 'WAITING'
  | 'FAILED';
```

### API Endpoints

**GET /api/tasks**
- Query params: `?page=1&pageSize=50&search=query&session=id&status=TODO,IN_PROGRESS&type=feature,fix&sortBy=updated&sortDir=desc`
- Response: `{ tasks: Task[], total: number, page: number, pageSize: number }`

**POST /api/tasks**
- Body: `{ title: string, session: string, type?: TaskType, status?: TaskStatus, implementation_notes?: string, depends_on?: number[] }`
- Response: `{ task: Task }`

**PUT /api/tasks/:id**
- Body: Same as POST (partial update supported)
- Response: `{ task: Task }`

**DELETE /api/tasks/:id**
- Response: `{ success: boolean }`

**POST /api/tasks/:id/move**
- Body: `{ to_session: string }`
- Response: `{ task: Task }`

---

## UI States & Edge Cases

### Loading States
- **Initial Load**: Full-page skeleton with table outline
- **Pagination**: Skeleton rows replacing current rows
- **Search/Filter**: Overlay spinner on table
- **Panel Load**: Skeleton form in side panel
- **Button Action**: Button shows spinner, text changes to "Saving..."

### Empty States
- **No Tasks Ever**: "No tasks yet. Create your first task to get started!" + illustration + CTA button
- **No Search Results**: "No tasks match '{query}'. Try different keywords." + Clear search button
- **No Filtered Results**: "No tasks match your filters. Try adjusting them." + Clear filters button

### Error States
- **Network Error**: "Unable to load tasks. Check your connection and try again." + Retry button
- **Permission Error**: "You don't have permission to view these tasks." + Contact admin link
- **Validation Error**: Inline errors below form fields with red text and icon
- **Server Error**: "Something went wrong. Our team has been notified." + Retry button

### Edge Cases
- **Circular Dependencies**: Validate on frontend and backend, show error: "Cannot add dependency: would create circular reference"
- **Session Deleted**: If task's session is deleted, show "Unknown Session" with warning icon
- **Very Long Title**: Truncate with ellipsis, show full title in tooltip
- **Very Long Notes**: Use expandable textarea with "Show more" button
- **1000+ Tasks**: Virtualized rendering kicks in, pagination required
- **Slow Network**: Show loading indicators, cache previous results
- **Concurrent Edits**: Optimistic locking, show conflict message if detected
- **Large Dependencies List**: Multi-select with search, show count badge

---

## Accessibility Requirements (WCAG 2.1 AA)

### Keyboard Navigation
- **Tab**: Navigate through interactive elements
- **Shift+Tab**: Navigate backwards
- **Enter**: Activate buttons, select dropdown options
- **Space**: Toggle checkboxes, open dropdowns
- **Escape**: Close modals, dropdowns, side panel
- **Arrow Keys**: Navigate dropdown options, table rows
- **Ctrl/Cmd+F**: Focus search bar (global shortcut)

### Screen Reader Support
- **ARIA Labels**: All interactive elements have descriptive labels
- **ARIA Live Regions**: Toast notifications, dynamic updates
- **ARIA Roles**: dialog, listbox, option, table, row, cell
- **Focus Management**: Trap focus in modals, restore focus on close
- **Announcements**: "Task created", "Filter applied", "Page 3 of 12"

### Visual Accessibility
- **Color Contrast**: 4.5:1 for text, 3:1 for UI components
- **Focus Indicators**: Visible 2px outline on all interactive elements
- **Text Size**: Minimum 16px, scalable with browser zoom
- **Touch Targets**: Minimum 44×44px for mobile
- **Color Independence**: Don't rely solely on color (use icons + text)

### Motion Accessibility
- **Respect prefers-reduced-motion**: Disable animations
- **Fallback Transitions**: Instant state changes if motion disabled
- **Pause/Stop**: Allow users to pause auto-advancing content

---

## Visual Design System

### Color Palette
```css
/* Primary Actions */
--primary: #3b82f6;          /* Blue */
--primary-hover: #2563eb;
--primary-light: #dbeafe;

/* Success */
--success: #10b981;          /* Green */
--success-light: #d1fae5;

/* Error */
--error: #ef4444;            /* Red */
--error-light: #fee2e2;

/* Warning */
--warning: #f59e0b;          /* Amber */
--warning-light: #fef3c7;

/* Neutral */
--gray-50: #f9fafb;
--gray-100: #f3f4f6;
--gray-200: #e5e7eb;
--gray-300: #d1d5db;
--gray-400: #9ca3af;
--gray-500: #6b7280;
--gray-600: #4b5563;
--gray-700: #374151;
--gray-800: #1f2937;
--gray-900: #111827;

/* Status Colors */
--status-todo: #8b5cf6;      /* Purple */
--status-in-progress: #3b82f6; /* Blue */
--status-done: #10b981;      /* Green */
--status-blocked: #ef4444;   /* Red */
--status-cancelled: #6b7280; /* Gray */
```

### Typography
```css
/* Font Family */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* Line Heights */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;
```

### Spacing
```css
/* Spacing Scale (Tailwind-like) */
--spacing-0: 0;
--spacing-1: 0.25rem;  /* 4px */
--spacing-2: 0.5rem;   /* 8px */
--spacing-3: 0.75rem;  /* 12px */
--spacing-4: 1rem;     /* 16px */
--spacing-5: 1.25rem;  /* 20px */
--spacing-6: 1.5rem;   /* 24px */
--spacing-8: 2rem;     /* 32px */
--spacing-10: 2.5rem;  /* 40px */
--spacing-12: 3rem;    /* 48px */
--spacing-16: 4rem;    /* 64px */
```

### Border Radius
```css
--radius-sm: 0.25rem;  /* 4px */
--radius-md: 0.375rem; /* 6px */
--radius-lg: 0.5rem;   /* 8px */
--radius-xl: 0.75rem;  /* 12px */
--radius-full: 9999px; /* Fully rounded */
```

### Shadows
```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
```

---

## Responsive Breakpoints

```css
/* Mobile First Approach */
--breakpoint-sm: 640px;   /* Small devices */
--breakpoint-md: 768px;   /* Medium devices */
--breakpoint-lg: 1024px;  /* Large devices */
--breakpoint-xl: 1280px;  /* Extra large devices */
--breakpoint-2xl: 1536px; /* 2X large devices */
```

### Layout Adaptations

**Mobile (< 640px)**:
- Stack toolbar vertically
- Hide some table columns (Type, Updated)
- Show task cards instead of table rows
- Full-width side panel (covers entire screen)
- Bottom sheet for filters
- Larger touch targets (48×48px minimum)

**Tablet (640px - 1024px)**:
- Horizontal toolbar with wrapped filters
- Show main columns (ID, Title, Session, Status)
- Side panel covers 60% of screen
- Dropdowns become modals

**Desktop (> 1024px)**:
- Full horizontal toolbar
- Show all columns
- Side panel is 400px fixed width
- Hover states enabled
- Keyboard shortcuts active

---

## Performance Optimization

### Rendering Optimization
- **React.memo**: Memoize TaskRow components
- **useMemo**: Memoize filtered/sorted task lists
- **useCallback**: Memoize event handlers
- **Code Splitting**: Lazy load TaskDetailPanel
- **Virtualization**: Use react-window for 1000+ rows

### Network Optimization
- **Debounced Search**: 300ms delay
- **Request Cancellation**: Cancel previous search requests
- **Pagination**: Load 50 tasks at a time
- **Caching**: Cache task list in React Query
- **Optimistic Updates**: Immediate UI updates, rollback on error
- **Batch Updates**: Group multiple updates into single API call

### Bundle Size
- **Tree Shaking**: Remove unused code
- **Code Splitting**: Split by route
- **Lazy Loading**: Load heavy components on demand
- **SVG Icons**: Use inline SVG instead of icon font
- **Image Optimization**: Use WebP, lazy load images

### Metrics Goals
- **First Contentful Paint (FCP)**: < 1.5s
- **Time to Interactive (TTI)**: < 3.5s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Cumulative Layout Shift (CLS)**: < 0.1
- **First Input Delay (FID)**: < 100ms

---

## Testing Strategy

### Unit Tests
- **Component Rendering**: Each component renders correctly
- **Event Handlers**: Clicks, keyboard events work
- **State Management**: Hooks update state correctly
- **Form Validation**: Validation logic works
- **Utility Functions**: Search, filter, sort functions

### Integration Tests
- **User Flows**: Complete flows from start to finish
- **API Integration**: Mocked API responses
- **Navigation**: Routing works correctly
- **State Persistence**: State survives page reload

### E2E Tests
- **Critical Paths**: 
  - Create task
  - Edit task
  - Delete task
  - Search and filter
  - Move task between sessions
- **Cross-Browser**: Chrome, Firefox, Safari, Edge
- **Responsive**: Mobile, tablet, desktop

### Accessibility Tests
- **Automated**: axe-core, jest-axe
- **Manual**: Keyboard navigation, screen reader testing
- **Contrast**: Color contrast validation

---

## Implementation Plan (Phased Approach)

### Phase 1: Foundation (Tasks 1-5)
- [ ] **Task 1**: Set up TaskManagementPage component
- [ ] **Task 2**: Create TaskToolbar with search (no autocomplete yet)
- [ ] **Task 3**: Implement TaskListView with TanStack Table
- [ ] **Task 4**: Add basic pagination
- [ ] **Task 5**: Integrate with API (GET /api/tasks)

**Deliverable**: Basic task list that loads and displays tasks

---

### Phase 2: Search & Filter (Tasks 6-10)
- [ ] **Task 6**: Add autocomplete to SearchBar
- [ ] **Task 7**: Implement session filter dropdown
- [ ] **Task 8**: Implement status filter dropdown
- [ ] **Task 9**: Implement type filter dropdown
- [ ] **Task 10**: Add filter logic and API integration

**Deliverable**: Fully functional search and filtering

---

### Phase 3: Task Details (Tasks 11-15)
- [ ] **Task 11**: Create TaskDetailPanel component
- [ ] **Task 12**: Build TaskForm with all fields
- [ ] **Task 13**: Add form validation
- [ ] **Task 14**: Integrate with API (PUT /api/tasks/:id)
- [ ] **Task 15**: Add animations (slide-in/out)

**Deliverable**: Side panel for viewing and editing task details

---

### Phase 4: Create & Delete (Tasks 16-20)
- [ ] **Task 16**: Add "New Task" button
- [ ] **Task 17**: Implement create task flow (POST /api/tasks)
- [ ] **Task 18**: Add delete task action (DELETE /api/tasks/:id)
- [ ] **Task 19**: Add confirmation modal for delete
- [ ] **Task 20**: Add toast notifications

**Deliverable**: Full CRUD operations for tasks

---

### Phase 5: Advanced Features (Tasks 21-25)
- [ ] **Task 21**: Implement drag-and-drop for moving tasks
- [ ] **Task 22**: Add move task API integration
- [ ] **Task 23**: Implement sorting (click column headers)
- [ ] **Task 24**: Add row selection (checkboxes)
- [ ] **Task 25**: Add bulk actions (delete, move)

**Deliverable**: Advanced task management features

---

### Phase 6: Polish & Optimization (Tasks 26-30)
- [ ] **Task 26**: Add all Framer Motion animations
- [ ] **Task 27**: Implement virtualization for large lists
- [ ] **Task 28**: Add loading/error/empty states
- [ ] **Task 29**: Responsive design (mobile/tablet)
- [ ] **Task 30**: Accessibility audit and fixes

**Deliverable**: Production-ready, polished UI

---

### Phase 7: Testing & Launch (Tasks 31-35)
- [ ] **Task 31**: Write unit tests for all components
- [ ] **Task 32**: Write integration tests for user flows
- [ ] **Task 33**: Write E2E tests for critical paths
- [ ] **Task 34**: Performance optimization (bundle size, rendering)
- [ ] **Task 35**: Documentation and deployment

**Deliverable**: Tested, optimized, and deployed feature

---

## Success Metrics

### User Engagement
- **Task View Rate**: % of users who view tasks page
- **Search Usage**: % of sessions using search
- **Filter Usage**: % of sessions using filters
- **Edit Rate**: % of tasks edited
- **Creation Rate**: Tasks created per user per day

### Performance
- **Page Load Time**: < 2 seconds
- **Search Response Time**: < 500ms
- **API Response Time**: < 200ms (p95)
- **Animation FPS**: Maintain 60fps

### Quality
- **Accessibility Score**: 100/100 (Lighthouse)
- **Zero Critical Bugs**: No blockers in production
- **User Satisfaction**: 4.5+ / 5.0 rating
- **Test Coverage**: > 85%

---

## Future Enhancements (Post-MVP)

### Phase 8: Advanced Features
- **Kanban Board View**: Alternative view with drag-and-drop columns
- **Task Templates**: Save and reuse task structures
- **Bulk Import**: Import tasks from CSV/JSON
- **Bulk Export**: Export tasks to CSV/Excel
- **Task Comments**: Add threaded comments to tasks
- **Task Attachments**: Attach files to tasks
- **Task History**: View audit log of all changes
- **Task Dependencies Visualization**: Graph view of dependencies
- **Advanced Search**: Boolean operators, saved searches
- **Custom Fields**: User-defined task fields
- **Task Labels/Tags**: Additional categorization
- **Notifications**: Real-time updates for task changes
- **Collaboration**: Multiple users editing same task

### Phase 9: Integration
- **GitHub Integration**: Sync with GitHub issues/PRs
- **Slack Integration**: Task notifications in Slack
- **Email Notifications**: Email for task assignments
- **Webhook Support**: Trigger external services
- **API Enhancements**: GraphQL API for flexible queries

---

## Conclusion

This specification provides a comprehensive blueprint for building a world-class task management interface for planloop. By following 2025 UX best practices, leveraging modern technologies (React, TanStack Table, Framer Motion), and prioritizing accessibility and performance, we will deliver a delightful user experience that enhances productivity.

The phased implementation approach ensures steady progress with clear milestones and deliverables at each stage. Each phase builds upon the previous one, allowing for iterative testing and refinement.

**Let's build something amazing!** 🚀

---

## Appendix: Technical Stack

### Frontend
- **Framework**: React 18+
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **Animations**: Framer Motion
- **Table**: TanStack Table v8
- **State Management**: React Query + Context API
- **Routing**: React Router v6
- **Form Handling**: React Hook Form
- **Validation**: Zod
- **HTTP Client**: Axios or Fetch API
- **Build Tool**: Vite

### Backend (API)
- **Framework**: FastAPI (Python)
- **Database**: (Assumed from planloop architecture)
- **API Format**: REST JSON
- **Authentication**: JWT or session-based

### Development Tools
- **Linting**: ESLint + Prettier
- **Testing**: Vitest + Testing Library + Playwright
- **Type Checking**: TypeScript strict mode
- **Git Hooks**: Husky + lint-staged
- **CI/CD**: GitHub Actions

---

**End of Specification**
