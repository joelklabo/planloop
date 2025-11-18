import { motion } from 'framer-motion'
import { useSessions } from '../hooks/useSessions'
import SessionCard from '../components/dashboard/SessionCard'

export default function SessionsPage() {
  const { sessions, loading, error, refetch } = useSessions()

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
      className="p-8 max-w-7xl mx-auto"
    >
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
            Sessions
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage and monitor your planloop sessions
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

      {/* Loading State */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700"
            >
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4"></div>
                <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-full"></div>
                <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-2/3"></div>
              </div>
            </motion.div>
          ))}
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
                Failed to load sessions
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

      {/* Empty State */}
      {!loading && !error && sessions.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-16"
        >
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            No sessions found
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Create your first session using the planloop CLI
          </p>
          <code className="inline-block bg-gray-100 dark:bg-gray-800 px-4 py-2 rounded-lg text-sm">
            planloop status
          </code>
        </motion.div>
      )}

      {/* Sessions Grid */}
      {!loading && !error && sessions.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {sessions.map((session, index) => (
            <SessionCard
              key={session.id}
              session={session}
              index={index}
            />
          ))}
        </motion.div>
      )}

      {/* Session Count */}
      {!loading && !error && sessions.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-8 text-center text-sm text-gray-600 dark:text-gray-400"
        >
          Showing {sessions.length} session{sessions.length !== 1 ? 's' : ''}
        </motion.div>
      )}
    </motion.div>
  )
}
