import type { User } from '@/types/user'
import { getApiBaseUrl } from './api'
import { getToken, setToken, removeToken } from './authStorage'

export const AuthService = {
  async login(username: string, password: string): Promise<User> {
    const response = await fetch(`${await getApiBaseUrl()}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.error || 'Login failed')
    }

    const data = await response.json()
    if (data.token) {
      setToken(data.token)
    }
    return data.user
  },

  async loginAsGuest(): Promise<User> {
    return this.login('Guest', 'Guest')
  },

  async logout(): Promise<void> {
    removeToken()
  },

  async getCurrentUser(): Promise<User | null> {
    const token = getToken()
    if (!token) {
      return null
    }

    try {
      const response = await fetch(`${await getApiBaseUrl()}/auth/me/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        removeToken()
        return null
      }

      const data = await response.json()
      return data.user
    } catch {
      removeToken()
      return null
    }
  },

  getToken(): string | null {
    return getToken()
  },
}
