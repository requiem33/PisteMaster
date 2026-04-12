import type { User } from '@/types/user'
import { getApiHeaders, getCsrfHeaders } from '@/utils/csrf'

function getApiBaseUrl(): string {
  // 在 Electron 桌面环境中，使用绝对 URL 到本地 Django 服务器
  if (typeof window !== 'undefined' && window.location.protocol === 'file:') {
    return 'http://127.0.0.1:8000/api'
  }
  
  // 在生产环境中使用环境变量，否则使用相对路径
  const baseUrl = import.meta.env.VITE_API_BASE_URL
  return baseUrl || '/api'
}

export const AuthService = {
  async login(username: string, password: string): Promise<User> {
    const apiBaseUrl = getApiBaseUrl()
    const response = await fetch(`${apiBaseUrl}/auth/login/`, {
      method: 'POST',
      headers: getApiHeaders(),
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.error || 'Login failed')
    }

    const data = await response.json()
    return data.user
  },

  async loginAsGuest(): Promise<User> {
    return this.login('Guest', 'Guest')
  },

  async logout(): Promise<void> {
    const apiBaseUrl = getApiBaseUrl()
    await fetch(`${apiBaseUrl}/auth/logout/`, {
      method: 'POST',
      headers: getCsrfHeaders(),
      credentials: 'include',
    })
  },

  async getCurrentUser(): Promise<User | null> {
    try {
      const apiBaseUrl = getApiBaseUrl()
      const response = await fetch(`${apiBaseUrl}/auth/me/`, {
        credentials: 'include',
      })

      if (!response.ok) {
        return null
      }

      const data = await response.json()
      return data.user
    } catch {
      return null
    }
  },
}