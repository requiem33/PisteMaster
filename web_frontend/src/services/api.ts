import { isElectron } from '@/utils/platform'
import { getToken } from './authStorage'

let apiUrlCache: string | null = null

export async function getApiBaseUrl(): Promise<string> {
  if (apiUrlCache) {
    return apiUrlCache
  }

  if (isElectron()) {
    try {
      const electron = window.electron as unknown as { cluster: { getApiUrl: () => Promise<string> } }
      const url = await electron.cluster.getApiUrl()
      apiUrlCache = url
      return url
    } catch (_error) {
      console.warn('Failed to get API URL from Electron, falling back to env')
    }
  }

  const envUrl = (import.meta.env.VITE_API_BASE_URL as string) || '/api'
  apiUrlCache = envUrl
  return envUrl
}

export async function getAuthHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export const API_BASE_URL = '/api'
