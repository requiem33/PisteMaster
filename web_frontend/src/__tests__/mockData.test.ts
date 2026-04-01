/**
 * Tests for mock data factories
 */

import { describe, it, expect } from 'vitest'
import {
  createMockTournament,
  createMockStage,
  createMockUser,
  createMockLoginCredentials,
  createMockAuthResponse,
  createMockPendingOperation,
  createMockSyncQueueEntry,
  createMockConflictItem,
  createMockNetworkStatus,
  createMockClusterNode,
  createMockClusterStatus,
  createMockTournamentList,
  createMockUserList,
} from '../test-utils/mockData'

describe('mockData factories', () => {
  describe('createMockTournament', () => {
    it('should create a valid tournament', () => {
      const tournament = createMockTournament()
      
      expect(tournament).toBeDefined()
      expect(tournament.id).toBeDefined()
      expect(tournament.tournament_name).toBeDefined()
      expect(tournament.start_date).toBeDefined()
      expect(tournament.end_date).toBeDefined()
      expect(['draft', 'active', 'completed']).toContain(tournament.status)
      expect(typeof tournament.is_synced).toBe('boolean')
    })
    
    it('should allow overrides', () => {
      const tournament = createMockTournament({
        tournament_name: 'Test Tournament',
        status: 'active',
      })
      
      expect(tournament.tournament_name).toBe('Test Tournament')
      expect(tournament.status).toBe('active')
    })
    
    it('should create unique IDs', () => {
      const t1 = createMockTournament()
      const t2 = createMockTournament()
      
      expect(t1.id).not.toBe(t2.id)
    })
  })
  
  describe('createMockStage', () => {
    it('should create a valid stage', () => {
      const stage = createMockStage()
      
      expect(stage).toBeDefined()
      expect(stage.id).toBeDefined()
      expect(stage.name).toBeDefined()
      expect(['pool', 'de']).toContain(stage.type)
      expect(stage.config).toBeDefined()
    })
    
    it('should allow overrides', () => {
      const stage = createMockStage({
        type: 'pool',
        config: { byes: 4, hits: 5 },
      })
      
      expect(stage.type).toBe('pool')
      expect(stage.config?.byes).toBe(4)
      expect(stage.config?.hits).toBe(5)
    })
  })
  
  describe('createMockUser', () => {
    it('should create a valid user', () => {
      const user = createMockUser()
      
      expect(user).toBeDefined()
      expect(user.id).toBeDefined()
      expect(user.username).toBeDefined()
      expect(user.firstName).toBeDefined()
      expect(user.lastName).toBeDefined()
      expect(['ADMIN', 'SCHEDULER']).toContain(user.role)
    })
    
    it('should allow overrides', () => {
      const user = createMockUser({
        username: 'testuser',
        role: 'ADMIN',
      })
      
      expect(user.username).toBe('testuser')
      expect(user.role).toBe('ADMIN')
    })
  })
  
  describe('createMockLoginCredentials', () => {
    it('should create valid credentials', () => {
      const creds = createMockLoginCredentials()
      
      expect(creds).toBeDefined()
      expect(creds.username).toBeDefined()
      expect(creds.password).toBeDefined()
    })
  })
  
  describe('createMockAuthResponse', () => {
    it('should create a valid auth response', () => {
      const response = createMockAuthResponse()
      
      expect(response).toBeDefined()
      expect(response.user).toBeDefined()
    })
    
    it('should allow error response', () => {
      const response = createMockAuthResponse({
        user: null,
        error: 'Invalid credentials',
      })
      
      expect(response.user).toBeNull()
      expect(response.error).toBe('Invalid credentials')
    })
  })
  
  describe('createMockPendingOperation', () => {
    it('should create a valid pending operation', () => {
      const op = createMockPendingOperation()
      
      expect(op).toBeDefined()
      expect(op.id).toBeDefined()
      expect(['INSERT', 'UPDATE', 'DELETE']).toContain(op.operation)
      expect(op.version).toBeGreaterThan(0)
    })
  })
  
  describe('createMockSyncQueueEntry', () => {
    it('should create a valid sync queue entry', () => {
      const entry = createMockSyncQueueEntry()
      
      expect(entry).toBeDefined()
      expect(entry.id).toBeDefined()
      expect(entry.operations).toBeInstanceOf(Array)
      expect(['pending', 'processing', 'completed', 'failed']).toContain(entry.status)
    })
  })
  
  describe('createMockConflictItem', () => {
    it('should create a valid conflict item', () => {
      const conflict = createMockConflictItem()
      
      expect(conflict).toBeDefined()
      expect(conflict.id).toBeDefined()
      expect(conflict.localData).toBeDefined()
      expect(conflict.remoteData).toBeDefined()
    })
  })
  
  describe('createMockNetworkStatus', () => {
    it('should create valid network status', () => {
      const status = createMockNetworkStatus()
      
      expect(status).toBeDefined()
      expect(typeof status.isOnline).toBe('boolean')
      expect(status.latency).toBeGreaterThanOrEqual(10)
    })
  })
  
  describe('createMockClusterNode', () => {
    it('should create a valid cluster node', () => {
      const node = createMockClusterNode()
      
      expect(node).toBeDefined()
      expect(node.nodeId).toBeDefined()
      expect(['master', 'follower', 'single']).toContain(node.role)
    })
  })
  
  describe('createMockClusterStatus', () => {
    it('should create valid cluster status', () => {
      const status = createMockClusterStatus()
      
      expect(status).toBeDefined()
      expect(['single', 'cluster']).toContain(status.mode)
      expect(status.peers).toBeInstanceOf(Array)
    })
  })
  
  describe('createMockTournamentList', () => {
    it('should create a list of tournaments', () => {
      const tournaments = createMockTournamentList(5)
      
      expect(tournaments).toHaveLength(5)
      expect(tournaments[0].id).toBeDefined()
    })
    
    it('should default to 5 tournaments', () => {
      const tournaments = createMockTournamentList()
      
      expect(tournaments).toHaveLength(5)
    })
  })
  
  describe('createMockUserList', () => {
    it('should create a list of users', () => {
      const users = createMockUserList(3)
      
      expect(users).toHaveLength(3)
      expect(users[0].username).toBeDefined()
    })
  })
})