/**
 * Smoke test to verify test infrastructure is working
 */
import { describe, it, expect } from 'vitest'

describe('Test Infrastructure', () => {
  it('should run basic test', () => {
    expect(true).toBe(true)
  })

  it('should support async tests', async () => {
    const result = await Promise.resolve(42)
    expect(result).toBe(42)
  })
})
