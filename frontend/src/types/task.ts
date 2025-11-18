/**
 * Task-related type definitions
 */

export type TaskType =
  | 'feature'
  | 'fix'
  | 'test'
  | 'chore'
  | 'refactor'
  | 'doc'
  | 'design'
  | 'investigate';

export type TaskStatus =
  | 'TODO'
  | 'IN_PROGRESS'
  | 'DONE'
  | 'BLOCKED'
  | 'CANCELLED'
  | 'SKIPPED'
  | 'OUT_OF_SCOPE'
  | 'WAITING'
  | 'FAILED';

export interface Task {
  id: number;
  title: string;
  session: string;
  session_name: string;
  type: TaskType;
  status: TaskStatus;
  depends_on: number[];
  implementation_notes: string | null;
  commit_sha: string | null;
  created_at: string;
  last_updated_at: string | null;
}

export interface TasksResponse {
  tasks: Task[];
  total: number;
  page: number;
  pageSize: number;
}

export interface TaskFilters {
  session?: string[];
  status?: TaskStatus[];
  type?: TaskType[];
}

export interface TaskSort {
  column: string;
  direction: 'asc' | 'desc';
}

export interface CreateTaskInput {
  title: string;
  session: string;
  type?: TaskType;
  status?: TaskStatus;
  implementation_notes?: string;
  depends_on?: number[];
}

export interface UpdateTaskInput extends Partial<CreateTaskInput> {
  id: number;
}

export interface MoveTaskInput {
  to_session: string;
}
