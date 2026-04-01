/**
 * Tests for authStore (Pinia store)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../../stores/authStore'
import { createMockUser } from '../../test-utils/mockData'

// Mock the AuthService
vi.mock('../../services/authService', () => ({
  AuthService: {
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}))

import { AuthService } from '../../services/authService'

describe('authStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const store = useAuthStore()

      expect(store.user).toBeNull()
      expect(store.loading).toBe(false)
    })

    it('should have correct computed properties when not authenticated', () => {
      const store = useAuthStore()

      expect(store.isAuthenticated).toBe(false)
      expect(store.isAdmin).toBe(false)
      expect(store.isScheduler).toBe(false)
      expect(store.username).toBe('')
    })
  })

  describe('login', () => {
    it('should set user on successful login', async () => {
      const mockUser = createMockUser({ role: 'ADMIN' })
      vi.mocked(AuthService.login).mockResolvedValue(mockUser)

      const store = useAuthStore()
      const result = await store.login('admin', 'password')

      expect(result).toBe(true)
      expect(store.user).toEqual(mockUser)
      expect(store.loading).toBe(false)
    })

    it('should return false on failed login', async () => {
      vi.mocked(AuthService.login).mockRejectedValue(new Error('Invalid credentials'))

      const store = useAuthStore()
      const result = await store.login('wrong', 'credentials')

      expect(result).toBe(false)
      expect(store.user).toBeNull()
      expect(store.loading).toBe(false)
    })

    it('should set loading state during login', async () => {
      const mockUser = createMockUser()
      vi.mocked(AuthService.login).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockUser), 100))
      )

      const store = useAuthStore()
      const loginPromise = store.login('user', 'password')

      expect(store.loading).toBe(true)
      await loginPromise
      expect(store.loading).toBe(false)
    })

    it('should allow re-login after fetchCurrentUser was skipped', async () => {
      const mockUser = createMockUser()
      vi.mocked(AuthService.login).mockResolvedValue(mockUser)

      const store = useAuthStore()
      
      // First logout to set internal flag
      vi.mocked(AuthService.logout).mockResolvedValue()
      await store.logout()

      // Clear the mock
      vi.mocked(AuthService.getCurrentUser).mockClear()

      // fetchCurrentUser should not call API after logout
      await store.fetchCurrentUser()
      expect(AuthService.getCurrentUser).not.toHaveBeenCalled()

      // But login should work
      const result = await store.login('user', 'password')
      expect(result).toBe(true)
      expect(store.user).toEqual(mockUser)
    })
  })

  describe('logout', () => {
    it('should clear user on logout', async () => {
      vi.mocked(AuthService.logout).mockResolvedValue()

      const store = useAuthStore()
      store.user = createMockUser()

      expect(store.user).not.toBeNull()

      await store.logout()

      expect(store.user).toBeNull()
    })

    it('should call AuthService.logout', async () => {
      vi.mocked(AuthService.logout).mockResolvedValue()

      const store = useAuthStore()
      await store.logout()

      expect(AuthService.logout).toHaveBeenCalled()
    })

    it('should set explicitLogout flag', async () => {
      vi.mocked(AuthService.logout).mockResolvedValue()

      const store = useAuthStore()
      store.user = createMockUser()

      await store.logout()

      // After logout, fetchCurrentUser should not call the API
      vi.mocked(AuthService.getCurrentUser).mockClear()
      await store.fetchCurrentUser()

      expect(AuthService.getCurrentUser).not.toHaveBeenCalled()
    })
  })

  describe('fetchCurrentUser', () => {
    it('should fetch and set current user', async () => {
      const mockUser = createMockUser()
      vi.mocked(AuthService.getCurrentUser).mockResolvedValue(mockUser)

      const store = useAuthStore()
      await store.fetchCurrentUser()

      expect(store.user).toEqual(mockUser)
      expect(store.loading).toBe(false)
    })

    it('should not fetch if user already exists', async () => {
      const mockUser = createMockUser()
      vi.mocked(AuthService.getCurrentUser).mockResolvedValue(mockUser)

      const store = useAuthStore()
      store.user = mockUser

      await store.fetchCurrentUser()

      expect(AuthService.getCurrentUser).not.toHaveBeenCalled()
    })

    it('should not fetch if explicitLogout is true', async () => {
      vi.mocked(AuthService.getCurrentUser).mockResolvedValue(createMockUser())

      const store = useAuthStore()
      // First set explicitLogout to true by logging out
      vi.mocked(AuthService.logout).mockResolvedValue()
      await store.logout()

      // Clear the mock
      vi.mocked(AuthService.getCurrentUser).mockClear()

      await store.fetchCurrentUser()

      expect(AuthService.getCurrentUser).not.toHaveBeenCalled()
    })

    it('should set user to null on error', async () => {
      vi.mocked(AuthService.getCurrentUser).mockRejectedValue(new Error('Not authenticated'))

      const store = useAuthStore()
      await store.fetchCurrentUser()

      expect(store.user).toBeNull()
    })
  })

  describe('computed properties', () => {
    it('should return correct username', () => {
      const store = useAuthStore()
      store.user = createMockUser({ username: 'testuser' })

      expect(store.username).toBe('testuser')
    })

    it('should return empty string for username when user is null', () => {
      const store = useAuthStore()

      expect(store.username).toBe('')
    })

    it('should return true for isAdmin when user is admin', () => {
      const store = useAuthStore()
      store.user = createMockUser({ role: 'ADMIN' })

      expect(store.isAdmin).toBe(true)
      expect(store.isScheduler).toBe(false)
    })

    it('should return true for isScheduler when user is scheduler', () => {
      const store = useAuthStore()
      store.user = createMockUser({ role: 'SCHEDULER' })

      expect(store.isScheduler).toBe(true)
      expect(store.isAdmin).toBe(false)
    })
  })
})