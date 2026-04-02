export type UserRole = 'ADMIN' | 'SCHEDULER' | 'GUEST'

export interface User {
  id: string
  username: string
  email?: string
  role: UserRole
  firstName: string
  lastName: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface AuthResponse {
  user: User | null
  error?: string
}