import type { User } from '@/types/user'
import { getCsrfToken } from '@/utils/csrf'

export const AuthService = {
  async login(username: string, password: string): Promise<User> {
    const response = await fetch('/api/auth/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
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

  async logout(): Promise<void> {
    await fetch('/api/auth/logout/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrfToken(),
      },
      credentials: 'include',
    })
  },

  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await fetch('/api/auth/me/', {
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