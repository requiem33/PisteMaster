import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types/user'
import { AuthService } from '@/services/authService'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)
  const explicitLogout = ref(false)

  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')
  const isScheduler = computed(() => user.value?.role === 'SCHEDULER')
  const username = computed(() => user.value?.username || '')

  const login = async (usernameInput: string, password: string): Promise<boolean> => {
    loading.value = true
    try {
      user.value = await AuthService.login(usernameInput, password)
      explicitLogout.value = false
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

  const fetchCurrentUser = async (): Promise<void> => {
    if (user.value || explicitLogout.value) {return}

    loading.value = true
    try {
      user.value = await AuthService.getCurrentUser()
    } catch {
      user.value = null
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    loading,
    isAuthenticated,
    isAdmin,
    isScheduler,
    username,
    login,
    logout,
    fetchCurrentUser,
  }
})