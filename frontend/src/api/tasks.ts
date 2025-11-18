/**
 * Task API client
 */

import type {
  Task,
  TasksResponse,
  CreateTaskInput,
  UpdateTaskInput,
  MoveTaskInput,
  TaskFilters,
  TaskSort,
} from '../types/task';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface GetTasksParams {
  page?: number;
  pageSize?: number;
  search?: string;
  filters?: TaskFilters;
  sort?: TaskSort;
}

export const tasksApi = {
  async getTasks(params: GetTasksParams = {}): Promise<TasksResponse> {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.set('page', String(params.page));
    if (params.pageSize) queryParams.set('pageSize', String(params.pageSize));
    if (params.search) queryParams.set('search', params.search);
    
    if (params.filters?.session?.length) {
      queryParams.set('session', params.filters.session.join(','));
    }
    if (params.filters?.status?.length) {
      queryParams.set('status', params.filters.status.join(','));
    }
    if (params.filters?.type?.length) {
      queryParams.set('type', params.filters.type.join(','));
    }
    
    if (params.sort) {
      queryParams.set('sortBy', params.sort.column);
      queryParams.set('sortDir', params.sort.direction);
    }
    
    const response = await fetch(`${API_BASE}/api/tasks?${queryParams}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch tasks: ${response.statusText}`);
    }
    return response.json();
  },

  async createTask(input: CreateTaskInput): Promise<Task> {
    const response = await fetch(`${API_BASE}/api/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    });
    if (!response.ok) {
      throw new Error(`Failed to create task: ${response.statusText}`);
    }
    const data = await response.json();
    return data.task;
  },

  async updateTask(input: UpdateTaskInput): Promise<Task> {
    const { id, ...body } = input;
    const response = await fetch(`${API_BASE}/api/tasks/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`Failed to update task: ${response.statusText}`);
    }
    const data = await response.json();
    return data.task;
  },

  async deleteTask(id: number): Promise<void> {
    const response = await fetch(`${API_BASE}/api/tasks/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`Failed to delete task: ${response.statusText}`);
    }
  },

  async moveTask(id: number, input: MoveTaskInput): Promise<Task> {
    const response = await fetch(`${API_BASE}/api/tasks/${id}/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    });
    if (!response.ok) {
      throw new Error(`Failed to move task: ${response.statusText}`);
    }
    const data = await response.json();
    return data.task;
  },

  async searchTasks(query: string): Promise<Task[]> {
    const response = await fetch(`${API_BASE}/api/tasks/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
      throw new Error(`Failed to search tasks: ${response.statusText}`);
    }
    const data = await response.json();
    return data.tasks || [];
  },
};
