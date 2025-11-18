/**
 * React Query hooks for task management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tasksApi } from '../api/tasks';
import type {
  CreateTaskInput,
  UpdateTaskInput,
  MoveTaskInput,
  TaskFilters,
  TaskSort,
} from '../types/task';

interface UseTasksParams {
  page?: number;
  pageSize?: number;
  search?: string;
  filters?: TaskFilters;
  sort?: TaskSort;
}

export function useTasks(params: UseTasksParams = {}) {
  return useQuery({
    queryKey: ['tasks', params],
    queryFn: () => tasksApi.getTasks(params),
    staleTime: 30000, // 30 seconds
  });
}

export function useTaskSearch(query: string) {
  return useQuery({
    queryKey: ['tasks', 'search', query],
    queryFn: () => tasksApi.searchTasks(query),
    enabled: query.length >= 2,
    staleTime: 10000,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (input: CreateTaskInput) => tasksApi.createTask(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}

export function useUpdateTask() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (input: UpdateTaskInput) => tasksApi.updateTask(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => tasksApi.deleteTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}

export function useMoveTask() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: MoveTaskInput }) =>
      tasksApi.moveTask(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}
