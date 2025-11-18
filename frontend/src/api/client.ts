import type { SessionSummary, SessionState, Task, Signal } from '../types/api'

const API_BASE = import.meta.env.DEV ? '/api' : '/api'

class APIError extends Error {
  status: number;
  response?: any;
  
  constructor(
    message: string,
    status: number,
    response?: any
  ) {
    super(message)
    this.name = 'APIError'
    this.status = status
    this.response = response
  }
}

async function fetchJSON<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`)
  
  if (!response.ok) {
    const text = await response.text()
    throw new APIError(
      `API error: ${response.statusText}`,
      response.status,
      text
    )
  }
  
  return response.json()
}

export const api = {
  sessions: {
    list: () => fetchJSON<SessionSummary[]>('/sessions'),
    
    get: (id: string) => fetchJSON<SessionState>(`/sessions/${id}`),
    
    getTasks: (id: string) => fetchJSON<Task[]>(`/sessions/${id}/tasks`),
    
    getSignals: (id: string) => fetchJSON<Signal[]>(`/sessions/${id}/signals`),
  },
}

export { APIError }
