import { http, HttpResponse } from 'msw'
import { mockTasks } from '../fixtures/tasks'

export const handlers = [
  // GET /api/tasks - List tasks with filtering and pagination
  http.get('/api/tasks', ({ request }) => {
    const url = new URL(request.url)
    const page = parseInt(url.searchParams.get('page') || '1')
    const pageSize = parseInt(url.searchParams.get('pageSize') || '50')
    const search = url.searchParams.get('search')
    const status = url.searchParams.get('status')
    const type = url.searchParams.get('type')

    let filtered = [...mockTasks]

    // Apply search filter
    if (search) {
      const searchLower = search.toLowerCase()
      filtered = filtered.filter(
        (task) =>
          task.title.toLowerCase().includes(searchLower) ||
          task.implementation_notes?.toLowerCase().includes(searchLower)
      )
    }

    // Apply status filter
    if (status) {
      const statuses = status.split(',')
      filtered = filtered.filter((task) => statuses.includes(task.status))
    }

    // Apply type filter
    if (type) {
      const types = type.split(',')
      filtered = filtered.filter((task) => types.includes(task.type))
    }

    // Paginate
    const start = (page - 1) * pageSize
    const end = start + pageSize
    const paginated = filtered.slice(start, end)

    return HttpResponse.json({
      tasks: paginated,
      total: filtered.length,
      page,
      pageSize,
    })
  }),

  // GET /api/tasks/search - Autocomplete search
  http.get('/api/tasks/search', ({ request }) => {
    const url = new URL(request.url)
    const q = url.searchParams.get('q') || ''
    const qLower = q.toLowerCase()

    const results = mockTasks
      .filter((task) => task.title.toLowerCase().includes(qLower))
      .slice(0, 10)

    return HttpResponse.json({ tasks: results })
  }),

  // GET /api/sessions - List sessions
  http.get('/api/sessions', () => {
    return HttpResponse.json([
      {
        id: 'test-session-1',
        description: 'Test Session 1',
        task_count: 10,
        signal_count: 2,
      },
      {
        id: 'test-session-2',
        description: 'Test Session 2',
        task_count: 5,
        signal_count: 0,
      },
    ])
  }),
]
