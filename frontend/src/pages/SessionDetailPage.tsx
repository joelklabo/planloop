import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useSession } from '../hooks/useSession'
import TaskTable from '../components/dashboard/TaskTable'
import SignalList from '../components/dashboard/SignalList'

export default function SessionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { session, loading, error, refetch } = useSession(id!)

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
      className="p-8 max-w-7xl mx-auto"
    >
      {/* Breadcrumb */}
      <div className="mb-6">
        <Link
          to="/sessions"
          className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Sessions
        </Link>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="space-y-6">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-1/2 mb-4"></div>
            <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4 mb-8"></div>
            <div className="h-64 bg-gray-300 dark:bg-gray-600 rounded"></div>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6"
        >
          <div className="flex items-start gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <h3 className="font-semibold text-red-900 dark:text-red-200 mb-1">
                Failed to load session
              </h3>
              <p className="text-sm text-red-700 dark:text-red-300">
                {error.message}
              </p>
              <button
                onClick={refetch}
                className="mt-3 text-sm font-medium text-red-600 dark:text-red-400 hover:underline"
              >
                Try again
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Session Content */}
      {!loading && !error && session && (
        <div className="space-y-6">
          {/* Header */}
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                {session.session}
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                {session.description}
              </p>
            </div>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={refetch}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </motion.button>
          </div>

          {/* Status Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6"
          >
            <div className="flex items-center gap-3">
              <span className="text-3xl">📌</span>
              <div>
                <div className="text-sm font-medium text-blue-900 dark:text-blue-200">
                  Current Status
                </div>
                <div className="text-lg font-bold text-blue-700 dark:text-blue-300">
                  {session.now.reason.replace(/_/g, ' ').toUpperCase()}
                </div>
                {session.now.task_id && (
                  <div className="text-sm text-blue-600 dark:text-blue-400 mt-1">
                    Working on task #{session.now.task_id}
                  </div>
                )}
              </div>
            </div>
          </motion.div>

          {/* Signals Section */}
          {session.signals.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700"
            >
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                Signals
              </h2>
              <SignalList signals={session.signals} />
            </motion.div>
          )}

          {/* Tasks Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700"
          >
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Tasks ({session.tasks.length})
            </h2>
            <TaskTable tasks={session.tasks} />
          </motion.div>

          {/* Metadata */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600 dark:text-gray-400"
          >
            <div>
              <span className="font-medium">Created:</span>{' '}
              {new Date(session.created_at).toLocaleString()}
            </div>
            <div>
              <span className="font-medium">Last Updated:</span>{' '}
              {new Date(session.last_updated_at).toLocaleString()}
            </div>
            <div>
              <span className="font-medium">Lock Holder:</span>{' '}
              {session.lock_holder || 'None'}
            </div>
          </div>
        </div>
      )}
    </motion.div>
  )
}
