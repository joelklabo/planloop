/**
 * Task Detail Panel - View and edit task details
 * Stub implementation for Phase 1
 */

import { motion } from 'framer-motion';
import type { Task } from '../../types/task';

interface TaskDetailPanelProps {
  task: Task | null;
  onClose: () => void;
  onSaved: () => void;
}

export default function TaskDetailPanel({ task, onClose }: TaskDetailPanelProps) {
  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
      />

      {/* Panel */}
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-white shadow-xl z-50 overflow-y-auto"
      >
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">
              {task ? 'Edit Task' : 'New Task'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Task detail form will be implemented in Phase 3
            </p>
            {task && (
              <div className="mt-4 p-4 bg-gray-50 rounded">
                <h3 className="font-medium text-gray-900 mb-2">Current Task:</h3>
                <p className="text-sm text-gray-700">{task.title}</p>
                <p className="text-xs text-gray-500 mt-1">ID: {task.id}</p>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </>
  );
}
