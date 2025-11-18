import { useState, useEffect } from 'react'
import { api } from '../api/client'
import type { SessionSummary } from '../types/api'

interface UseSessionsResult {
  sessions: SessionSummary[]
  loading: boolean
  error: Error | null
  refetch: () => void
}

export function useSessions(): UseSessionsResult {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [refetchTrigger, setRefetchTrigger] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function fetchSessions() {
      try {
        setLoading(true)
        setError(null)
        const data = await api.sessions.list()
        
        if (!cancelled) {
          setSessions(data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error('Failed to fetch sessions'))
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchSessions()

    return () => {
      cancelled = true
    }
  }, [refetchTrigger])

  const refetch = () => setRefetchTrigger(prev => prev + 1)

  return { sessions, loading, error, refetch }
}
