/**
 * Task Toolbar - Search with autocomplete, filters, and actions
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTaskSearch } from '../../hooks/useTasks';
import type { TaskFilters, TaskStatus, TaskType } from '../../types/task';

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
  filters,
  onFilterChange,
  onNewTask,
  totalTasks,
  filteredCount,
}: TaskToolbarProps) {
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [showStatusFilter, setShowStatusFilter] = useState(false);
  const [showTypeFilter, setShowTypeFilter] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const statusRef = useRef<HTMLDivElement>(null);
  const typeRef = useRef<HTMLDivElement>(null);

  const { data: suggestions = [] } = useTaskSearch(searchQuery);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowAutocomplete(false);
      }
      if (statusRef.current && !statusRef.current.contains(event.target as Node)) {
        setShowStatusFilter(false);
      }
      if (typeRef.current && !typeRef.current.contains(event.target as Node)) {
        setShowTypeFilter(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!showAutocomplete || suggestions.length === 0) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setActiveIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setActiveIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
          break;
        case 'Enter':
          e.preventDefault();
          if (activeIndex >= 0) {
            onSearchChange(suggestions[activeIndex].title);
            setShowAutocomplete(false);
          }
          break;
        case 'Escape':
          setShowAutocomplete(false);
          break;
      }
    },
    [showAutocomplete, suggestions, activeIndex, onSearchChange]
  );

  const toggleStatusFilter = (status: TaskStatus) => {
    const currentStatuses = filters.status || [];
    const newStatuses = currentStatuses.includes(status)
      ? currentStatuses.filter((s) => s !== status)
      : [...currentStatuses, status];
    onFilterChange({ ...filters, status: newStatuses });
  };

  const toggleTypeFilter = (type: TaskType) => {
    const currentTypes = filters.type || [];
    const newTypes = currentTypes.includes(type)
      ? currentTypes.filter((t) => t !== type)
      : [...currentTypes, type];
    onFilterChange({ ...filters, type: newTypes });
  };

  const hasActiveFilters =
    (filters.status && filters.status.length > 0) || (filters.type && filters.type.length > 0);

  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
        {/* Search Bar with Autocomplete */}
        <div ref={searchRef} className="relative flex-1 min-w-0">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                onSearchChange(e.target.value);
                setShowAutocomplete(true);
                setActiveIndex(-1);
              }}
              onFocus={() => setShowAutocomplete(true)}
              onKeyDown={handleKeyDown}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Search tasks..."
            />
          </div>

          <AnimatePresence>
            {showAutocomplete && searchQuery.length >= 2 && suggestions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.15 }}
                className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm"
              >
                {suggestions.slice(0, 10).map((task, index) => (
                  <button
                    key={task.id}
                    onClick={() => {
                      onSearchChange(task.title);
                      setShowAutocomplete(false);
                    }}
                    className={`${
                      index === activeIndex ? 'bg-blue-50' : 'hover:bg-gray-50'
                    } w-full text-left px-4 py-2 text-sm transition-colors`}
                  >
                    <div className="font-medium text-gray-900 truncate">{task.title}</div>
                    <div className="text-gray-500 text-xs mt-0.5">{task.session_name}</div>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Status Filter */}
        <div ref={statusRef} className="relative">
          <button
            onClick={() => setShowStatusFilter(!showStatusFilter)}
            className={`inline-flex items-center px-4 py-2 border ${
              filters.status && filters.status.length > 0
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 bg-white text-gray-700'
            } rounded-md text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 whitespace-nowrap`}
          >
            Status
            {filters.status && filters.status.length > 0 && (
              <span className="ml-2 bg-blue-600 text-white rounded-full px-2 py-0.5 text-xs">
                {filters.status.length}
              </span>
            )}
            <svg
              className={`ml-2 h-4 w-4 transition-transform ${showStatusFilter ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <AnimatePresence>
            {showStatusFilter && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.15 }}
                className="absolute z-10 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5"
              >
                <div className="py-1 max-h-60 overflow-auto">
                  {STATUS_OPTIONS.map((option) => (
                    <label
                      key={option.value}
                      className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={(filters.status || []).includes(option.value)}
                        onChange={() => toggleStatusFilter(option.value)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-3">{option.label}</span>
                    </label>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Type Filter */}
        <div ref={typeRef} className="relative">
          <button
            onClick={() => setShowTypeFilter(!showTypeFilter)}
            className={`inline-flex items-center px-4 py-2 border ${
              filters.type && filters.type.length > 0
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 bg-white text-gray-700'
            } rounded-md text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 whitespace-nowrap`}
          >
            Type
            {filters.type && filters.type.length > 0 && (
              <span className="ml-2 bg-blue-600 text-white rounded-full px-2 py-0.5 text-xs">
                {filters.type.length}
              </span>
            )}
            <svg
              className={`ml-2 h-4 w-4 transition-transform ${showTypeFilter ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <AnimatePresence>
            {showTypeFilter && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.15 }}
                className="absolute z-10 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5"
              >
                <div className="py-1 max-h-60 overflow-auto">
                  {TYPE_OPTIONS.map((option) => (
                    <label
                      key={option.value}
                      className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={(filters.type || []).includes(option.value)}
                        onChange={() => toggleTypeFilter(option.value)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-3">{option.label}</span>
                    </label>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* New Task Button */}
        <button
          onClick={onNewTask}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 whitespace-nowrap"
        >
          <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Task
        </button>
      </div>

      {/* Results Summary */}
      <div className="mt-3 flex items-center justify-between text-sm text-gray-600">
        <div>
          Showing <span className="font-medium">{filteredCount}</span> of{' '}
          <span className="font-medium">{totalTasks}</span> tasks
        </div>
        {hasActiveFilters && (
          <button
            onClick={() => onFilterChange({})}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}

const STATUS_OPTIONS: Array<{ value: TaskStatus; label: string }> = [
  { value: 'TODO', label: 'To Do' },
  { value: 'IN_PROGRESS', label: 'In Progress' },
  { value: 'DONE', label: 'Done' },
  { value: 'BLOCKED', label: 'Blocked' },
  { value: 'CANCELLED', label: 'Cancelled' },
  { value: 'WAITING', label: 'Waiting' },
  { value: 'FAILED', label: 'Failed' },
  { value: 'SKIPPED', label: 'Skipped' },
  { value: 'OUT_OF_SCOPE', label: 'Out of Scope' },
];

const TYPE_OPTIONS: Array<{ value: TaskType; label: string }> = [
  { value: 'feature', label: '✨ Feature' },
  { value: 'fix', label: '🐛 Fix' },
  { value: 'test', label: '🧪 Test' },
  { value: 'chore', label: '🔧 Chore' },
  { value: 'refactor', label: '♻️ Refactor' },
  { value: 'doc', label: '📝 Documentation' },
  { value: 'design', label: '🎨 Design' },
  { value: 'investigate', label: '🔍 Investigate' },
];
