import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import type { SessionSummary } from '../../types/api'

interface SessionCardProps {
  session: SessionSummary
  index: number
}

export default function SessionCard({ session, index }: SessionCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
    >
      <Link to={`/sessions/${session.id}`}>
        <motion.div
          whileHover={{ scale: 1.02, y: -4 }}
          whileTap={{ scale: 0.98 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700 transition-shadow hover:shadow-xl"
        >
          {/* Session ID/Title */}
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {session.id}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
              {session.description || 'No description'}
            </p>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-4">
            {/* Tasks */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                <span className="text-lg">📋</span>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {session.task_count}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Tasks
                </div>
              </div>
            </div>

            {/* Signals */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
                <span className="text-lg">🔔</span>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {session.signal_count}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Signals
                </div>
              </div>
            </div>
          </div>

          {/* View arrow */}
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end">
            <span className="text-sm font-medium text-blue-600 dark:text-blue-400 flex items-center gap-1">
              View Details
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </span>
          </div>
        </motion.div>
      </Link>
    </motion.div>
  )
}
