/**
 * Tests for tournament types
 */

import { describe, it, expect } from 'vitest'
import { createMockTournament, createMockStage, createMockTournamentList } from '../../test-utils/mockData'

describe('Tournament types', () => {
  describe('createMockTournament', () => {
    it('should create a valid tournament', () => {
      const tournament = createMockTournament()

      expect(tournament).toBeDefined()
      expect(tournament.id).toBeDefined()
      expect(tournament.tournament_name).toBeDefined()
      expect(['draft', 'active', 'completed']).toContain(tournament.status)
      expect(typeof tournament.is_synced).toBe('boolean')
    })

    it('should allow overriding properties', () => {
      const tournament = createMockTournament({
        tournament_name: 'Custom Tournament',
        status: 'active',
        is_synced: true,
      })

      expect(tournament.tournament_name).toBe('Custom Tournament')
      expect(tournament.status).toBe('active')
      expect(tournament.is_synced).toBe(true)
    })

    it('should generate unique IDs', () => {
      const t1 = createMockTournament()
      const t2 = createMockTournament()

      expect(t1.id).not.toBe(t2.id)
    })

    it('should generate valid dates', () => {
      const tournament = createMockTournament()

      expect(tournament.start_date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      expect(tournament.end_date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    })
  })

  describe('createMockStage', () => {
    it('should create a valid stage', () => {
      const stage = createMockStage()

      expect(stage).toBeDefined()
      expect(stage.id).toBeDefined()
      expect(stage.name).toBeDefined()
      expect(['pool', 'de']).toContain(stage.type)
    })

    it('should allow overriding stage type', () => {
      const poolStage = createMockStage({ type: 'pool' })
      const deStage = createMockStage({ type: 'de' })

      expect(poolStage.type).toBe('pool')
      expect(deStage.type).toBe('de')
    })

    it('should allow overriding config', () => {
      const stage = createMockStage({
        type: 'pool',
        config: {
          byes: 4,
          hits: 5,
        },
      })

      expect(stage.config?.byes).toBe(4)
      expect(stage.config?.hits).toBe(5)
    })
  })

  describe('createMockTournamentList', () => {
    it('should create a list of tournaments', () => {
      const tournaments = createMockTournamentList(5)

      expect(tournaments).toHaveLength(5)
      tournaments.forEach((t) => {
        expect(t.id).toBeDefined()
        expect(t.tournament_name).toBeDefined()
      })
    })

    it('should use default count of 5', () => {
      const tournaments = createMockTournamentList()

      expect(tournaments).toHaveLength(5)
    })

    it('should create unique tournaments', () => {
      const tournaments = createMockTournamentList(3)

      const ids = tournaments.map((t) => t.id)
      const uniqueIds = new Set(ids)

      expect(uniqueIds.size).toBe(3)
    })
  })
})