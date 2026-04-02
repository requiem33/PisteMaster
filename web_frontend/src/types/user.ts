export type UserRole = 'ADMIN' | 'SCHEDULER'

export interface User {
  id: string
  username: string
  email?: string
  role: UserRole
  firstName: string
  lastName: string
  isGuest?: false
}

export interface GuestUser {
  id: string
  username: string
  isGuest: true
}

export type AppUser = User | GuestUser

export function isGuestUser(user: AppUser | null): user is GuestUser {
  return user !== null && 'isGuest' in user && user.isGuest === true
}

export function isAuthenticatedUser(user: AppUser | null): user is User {
  return user !== null && !('isGuest' in user)
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface AuthResponse {
  user: User | null
  error?: string
}