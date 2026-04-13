import type {NetworkStatus} from '@/types/cluster'
import { getAuthHeaders } from './api'

class NetworkServiceClass {
  private status: NetworkStatus = {
    isOnline: navigator.onLine,
    lastOnline: navigator.onLine ? new Date() : null,
    lastOffline: null,
    latency: null,
  }
  private listeners: Set<(status: NetworkStatus) => void> = new Set()
  private latencyCheckInterval: ReturnType<typeof setInterval> | null = null

  constructor() {
    window.addEventListener('online', this.handleOnline)
    window.addEventListener('offline', this.handleOffline)
    this.startLatencyCheck()
  }

  getStatus(): NetworkStatus {
    return {...this.status}
  }

  isOnline(): boolean {
    return this.status.isOnline
  }

  subscribe(callback: (status: NetworkStatus) => void): () => void {
    this.listeners.add(callback)
    return () => {
      this.listeners.delete(callback)
    }
  }

  private notifyListeners(): void {
    const status = this.getStatus()
    this.listeners.forEach(callback => callback(status))
  }

  private handleOnline = (): void => {
    this.status.isOnline = true
    this.status.lastOnline = new Date()
    this.notifyListeners()
  }

  private handleOffline = (): void => {
    this.status.isOnline = false
    this.status.lastOffline = new Date()
    this.status.latency = null
    this.notifyListeners()
  }

  async checkLatency(url: string): Promise<number> {
    const start = performance.now()
    try {
      const response = await fetch(url, {
        method: 'HEAD',
        cache: 'no-cache',
      })
      if (response.ok) {
        const latency = performance.now() - start
        this.status.latency = latency
        this.notifyListeners()
        return latency
      }
    } catch {
      this.status.latency = null
    }
    return -1
  }

  private startLatencyCheck(): void {
    if (this.latencyCheckInterval) {
      clearInterval(this.latencyCheckInterval)
    }
    this.latencyCheckInterval = setInterval(() => {
      if (this.status.isOnline) {
        this.checkLatency(window.location.origin + '/api/cluster/health').catch(() => {
          this.status.latency = null
        })
      }
    }, 30000)
  }

  stopLatencyCheck(): void {
    if (this.latencyCheckInterval) {
      clearInterval(this.latencyCheckInterval)
      this.latencyCheckInterval = null
    }
  }

  async fetchWithRetry<T>(
    url: string,
    options: RequestInit = {},
    retries = 3,
    retryDelay = 1000
  ): Promise<T> {
    let lastError: Error | null = null
    let authHeaders: Record<string, string> = { 'Content-Type': 'application/json' }
    try {
      authHeaders = await getAuthHeaders()
    } catch {
      // Fallback to basic headers if getAuthHeaders fails
    }
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const response = await fetch(url, {
          ...options,
          headers: {
            ...authHeaders,
            ...options.headers,
          },
        })
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        return (await response.json()) as T
      } catch (error) {
        lastError = error as Error
        if (attempt < retries - 1) {
          await new Promise(resolve => setTimeout(resolve, retryDelay * (attempt + 1)))
        }
      }
    }
    throw lastError || new Error('Network request failed')
  }

  destroy(): void {
    window.removeEventListener('online', this.handleOnline)
    window.removeEventListener('offline', this.handleOffline)
    this.stopLatencyCheck()
    this.listeners.clear()
  }
}

export const NetworkService = new NetworkServiceClass()