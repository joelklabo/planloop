import { motion } from 'framer-motion'

export default function KanbanPage() {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
      className="p-8"
    >
      <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-6">
        Kanban Board
      </h1>
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
      >
        <p className="text-gray-600 dark:text-gray-300">
          Kanban board will be implemented in Phase 3 (W3.1-W3.4)
        </p>
      </motion.div>
    </motion.div>
  )
}
