import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { GuestUser, AppUser } from '@/types/user'
import { isGuestUser } from '@/types/user'
import { AuthService } from '@/services/authService'
import { LocalAuthService } from '@/services/localAuthService'
import { isElectron } from '@/utils/platform'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AppUser | null>(null)
  const loading = ref(false)
  const explicitLogout = ref(false)

  const isAuthenticated = computed(() => !!user.value && !isGuestUser(user.value))
  const isGuest = computed(() => isGuestUser(user.value))
  const isDesktop = computed(() => isElectron())
  const isAdmin = computed(() => !isGuestUser(user.value) && user.value?.role === 'ADMIN')
  const isScheduler = computed(() => !isGuestUser(user.value) && user.value?.role === 'SCHEDULER')
  const username = computed(() => user.value?.username || '')

  const initGuestUser = (): void => {
    if (!isElectron()) {
      return
    }
    const guestUser = LocalAuthService.getLocalUser()
    if (guestUser) {
      user.value = guestUser as GuestUser
    }
  }

  const login = async (usernameInput: string, password: string): Promise<boolean> => {
    loading.value = true
    try {
      const authenticatedUser = await AuthService.login(usernameInput, password)
      user.value = authenticatedUser
      explicitLogout.value = false
      LocalAuthService.clearLocalUser()
      return true
    } catch {
      user.value = null
      return false
    } finally {
      loading.value = false
    }
  }

  const logout = async (): Promise<void> => {
    try {
      await AuthService.logout()
    } finally {
      user.value = null
      explicitLogout.value = true
    }
  }

  const updateGuestUsername = (newUsername: string): boolean => {
    if (!isGuestUser(user.value)) {
      return false
    }
    const updated = LocalAuthService.updateLocalUsername(newUsername)
    if (updated) {
      user.value = updated as GuestUser
      return true
    }
    return false
  }

  const fetchCurrentUser = async (): Promise<void> => {
    if (user.value || explicitLogout.value) {
      return
    }

    loading.value = true
    try {
      const currentUser = await AuthService.getCurrentUser()
      if (currentUser) {
        user.value = currentUser
      } else if (isElectron()) {
        initGuestUser()
      }
    } catch {
      if (isElectron()) {
        initGuestUser()
      } else {
        user.value = null
      }
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    loading,
    isAuthenticated,
    isGuest,
    isDesktop,
    isAdmin,
    isScheduler,
    username,
    login,
    logout,
    fetchCurrentUser,
    initGuestUser,
    updateGuestUsername,
  }
})