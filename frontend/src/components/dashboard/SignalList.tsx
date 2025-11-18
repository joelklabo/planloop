import { motion } from 'framer-motion'
import type { Signal, SignalLevel } from '../../types/api'

interface SignalListProps {
  signals: Signal[]
}

const levelColors: Record<SignalLevel, string> = {
  'blocker': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300 border-red-300 dark:border-red-700',
  'high': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700',
  'info': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300 border-blue-300 dark:border-blue-700',
}

const levelIcons: Record<SignalLevel, string> = {
  'blocker': '🚨',
  'high': '⚠️',
  'info': 'ℹ️',
}

export default function SignalList({ signals }: SignalListProps) {
  const activeSignals = signals.filter(s => s.open)

  if (activeSignals.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-4xl mb-2">✅</div>
        <div className="text-gray-500 dark:text-gray-400">
          No active signals
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {activeSignals.map((signal, index) => (
        <motion.div
          key={signal.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
          className={`p-4 rounded-lg border-2 ${levelColors[signal.level]}`}
        >
          <div className="flex items-start gap-3">
            <span className="text-2xl">{levelIcons[signal.level]}</span>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="font-semibold">
                  {signal.title}
                </h4>
                <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-white/50 dark:bg-black/20">
                  {signal.type}
                </span>
              </div>
              <p className="text-sm opacity-90">
                {signal.message}
              </p>
              {signal.link && (
                <a
                  href={signal.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium hover:underline mt-2 inline-block"
                >
                  View details →
                </a>
              )}
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  )
}
