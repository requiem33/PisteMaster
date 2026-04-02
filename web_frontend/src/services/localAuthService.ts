import { v4 as uuidv4 } from 'uuid'
import { isElectron } from '@/utils/platform'

export interface LocalUser {
  id: string
  isGuest: true
  username: string
}

const LOCAL_USER_KEY = 'piste_local_user'

export const LocalAuthService = {
  isAvailable(): boolean {
    return isElectron()
  },

  getLocalUser(): LocalUser | null {
    if (!isElectron()) {
      return null
    }

    const stored = localStorage.getItem(LOCAL_USER_KEY)
    if (stored) {
      try {
        return JSON.parse(stored) as LocalUser
      } catch {
        localStorage.removeItem(LOCAL_USER_KEY)
      }
    }

    const guestUser: LocalUser = {
      id: uuidv4(),
      isGuest: true,
      username: `Guest_${uuidv4().slice(0, 6)}`,
    }
    localStorage.setItem(LOCAL_USER_KEY, JSON.stringify(guestUser))
    return guestUser
  },

  clearLocalUser(): void {
    localStorage.removeItem(LOCAL_USER_KEY)
  },

  updateLocalUsername(username: string): LocalUser | null {
    if (!isElectron()) {
      return null
    }

    const user = this.getLocalUser()
    if (!user) {
      return null
    }

    user.username = username
    localStorage.setItem(LOCAL_USER_KEY, JSON.stringify(user))
    return user
  },
}