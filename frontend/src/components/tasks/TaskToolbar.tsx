/**
 * Task Toolbar - Search, filters, and actions
 * Stub implementation for Phase 1
 */

import type { TaskFilters } from '../../types/task';

interface TaskToolbarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  filters: TaskFilters;
  onFilterChange: (filters: TaskFilters) => void;
  onNewTask: () => void;
  totalTasks: number;
  filteredCount: number;
}

export default function TaskToolbar({
  searchQuery,
  onSearchChange,
  onNewTask,
  totalTasks,
  filteredCount,
}: TaskToolbarProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
        {/* Basic Search Bar */}
        <div className="relative flex-1 min-w-0">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="block w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="Search tasks..."
          />
        </div>

        {/* New Task Button */}
        <button
          onClick={onNewTask}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
        >
          New Task
        </button>
      </div>

      {/* Results Summary */}
      <div className="mt-3 text-sm text-gray-600">
        Showing <span className="font-medium">{filteredCount}</span> of{' '}
        <span className="font-medium">{totalTasks}</span> tasks
      </div>
    </div>
  );
}
