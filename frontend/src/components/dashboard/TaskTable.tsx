import { motion } from 'framer-motion'
import type { Task, TaskStatus } from '../../types/api'

interface TaskTableProps {
  tasks: Task[]
}

const statusColors: Record<TaskStatus, string> = {
  'TODO': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  'IN_PROGRESS': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  'DONE': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  'BLOCKED': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  'SKIPPED': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  'OUT_OF_SCOPE': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  'CANCELLED': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  'FAILED': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  'WAITING': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
}

const typeEmojis: Record<string, string> = {
  'test': '🧪',
  'fix': '🔧',
  'refactor': '♻️',
  'feature': '✨',
  'doc': '📝',
  'chore': '🧹',
  'design': '🎨',
  'investigate': '🔍',
}

export default function TaskTable({ tasks }: TaskTableProps) {
  if (tasks.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        No tasks yet
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              ID
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Title
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Type
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          {tasks.map((task, index) => (
            <motion.tr
              key={task.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                #{task.id}
              </td>
              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                {task.title}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm">
                <span className="flex items-center gap-1">
                  <span>{typeEmojis[task.type] || '📌'}</span>
                  <span className="text-gray-600 dark:text-gray-400">{task.type}</span>
                </span>
              </td>
              <td className="px-4 py-3 whitespace-nowrap">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[task.status]}`}>
                  {task.status}
                </span>
              </td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
