import { useState, useEffect } from 'react'
import { api } from '../api/client'
import type { SessionState } from '../types/api'

interface UseSessionResult {
  session: SessionState | null
  loading: boolean
  error: Error | null
  refetch: () => void
}

export function useSession(id: string): UseSessionResult {
  const [session, setSession] = useState<SessionState | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [refetchTrigger, setRefetchTrigger] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function fetchSession() {
      try {
        setLoading(true)
        setError(null)
        const data = await api.sessions.get(id)
        
        if (!cancelled) {
          setSession(data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error('Failed to fetch session'))
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchSession()

    return () => {
      cancelled = true
    }
  }, [id, refetchTrigger])

  const refetch = () => setRefetchTrigger(prev => prev + 1)

  return { session, loading, error, refetch }
}
