/**
 * Tests for test utilities
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { createTestPinia, createTestRouter, mockLocalStorage, mockSessionStorage, waitFor } from '../test-utils/test-utils'

describe('test-utils', () => {
  describe('createTestPinia', () => {
    it('should create a pinia instance', () => {
      const pinia = createTestPinia()
      
      expect(pinia).toBeDefined()
      expect(pinia.state).toBeDefined()
    })
    
    it('should accept initial state', () => {
      const initialState = {
        tournament: { current: { id: 'test-id' } },
      }
      const pinia = createTestPinia(initialState)
      
      expect(pinia.state.value.tournament).toBeDefined()
      expect(pinia.state.value.tournament.current.id).toBe('test-id')
    })
  })
  
  describe('createTestRouter', () => {
    it('should create a router instance', () => {
      const router = createTestRouter()
      
      expect(router).toBeDefined()
      expect(router.push).toBeDefined()
    })
    
    it('should accept custom routes', () => {
      const router = createTestRouter([
        { path: '/test', component: { template: '<div>Test</div>' } },
      ])
      
      expect(router).toBeDefined()
      expect(router.getRoutes().length).toBeGreaterThan(0)
    })
  })
  
  describe('mockLocalStorage', () => {
    let storage: ReturnType<typeof mockLocalStorage>
    
    beforeEach(() => {
      storage = mockLocalStorage()
    })
    
    it('should store and retrieve values', () => {
      storage.setItem('key', 'value')
      
      expect(storage.getItem('key')).toBe('value')
    })
    
    it('should remove values', () => {
      storage.setItem('key', 'value')
      storage.removeItem('key')
      
      expect(storage.getItem('key')).toBeNull()
    })
    
    it('should clear all values', () => {
      storage.setItem('key1', 'value1')
      storage.setItem('key2', 'value2')
      storage.clear()
      
      expect(storage.getItem('key1')).toBeNull()
      expect(storage.getItem('key2')).toBeNull()
    })
    
    it('should track calls', () => {
      storage.setItem('key', 'value')
      
      expect(storage.setItem).toHaveBeenCalledWith('key', 'value')
    })
  })
  
  describe('mockSessionStorage', () => {
    let storage: ReturnType<typeof mockSessionStorage>
    
    beforeEach(() => {
      storage = mockSessionStorage()
    })
    
    it('should work like localStorage', () => {
      storage.setItem('key', 'value')
      
      expect(storage.getItem('key')).toBe('value')
    })
  })
  
  describe('waitFor', () => {
    it('should resolve when condition becomes true', async () => {
      let condition = false
      
      setTimeout(() => {
        condition = true
      }, 100)
      
      await expect(waitFor(() => condition)).resolves.toBeUndefined()
    })
    
    it('should reject on timeout', async () => {
      const condition = () => false
      
      await expect(waitFor(condition, 100)).rejects.toThrow('Wait timeout')
    })
  })
  
  describe('toBeValidUUID matcher', () => {
    it('should pass for valid UUIDs', () => {
      const validUUID = '123e4567-e89b-12d3-a456-426614174000'
      
      expect(validUUID).toBeValidUUID()
    })
    
    it('should fail for invalid UUIDs', () => {
      const invalidUUID = 'not-a-uuid'
      
      expect(() => {
        expect(invalidUUID).toBeValidUUID()
      }).toThrow()
    })
  })
})