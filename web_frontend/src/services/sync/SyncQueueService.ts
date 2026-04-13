import type {PendingOperation} from '@/types/cluster'
import {IndexedDBService} from '../storage/IndexedDBService'
import { getAuthHeaders } from '../api'

const MAX_RETRIES = 5
const RETRY_DELAYS = [1000, 2000, 5000, 10000, 30000]

export interface SyncQueueConfig {
  maxRetries: number
  retryDelays: number[]
  batchSize: number
}

const defaultConfig: SyncQueueConfig = {
  maxRetries: MAX_RETRIES,
  retryDelays: RETRY_DELAYS,
  batchSize: 10,
}

class SyncQueueServiceClass {
  private config: SyncQueueConfig
  private isProcessing = false
  private masterUrl: string | null = null
  private onOnlineCallback: (() => void) | null = null

  constructor(config: Partial<SyncQueueConfig> = {}) {
    this.config = {...defaultConfig, ...config}
  }

  setMasterUrl(url: string | null): void {
    this.masterUrl = url
  }

  async addPending(op: Omit<PendingOperation, 'id' | 'retries' | 'lastAttempt' | 'createdAt'>): Promise<string> {
    const operation: PendingOperation = {
      ...op,
      id: crypto.randomUUID(),
      retries: 0,
      lastAttempt: null,
      createdAt: new Date(),
      version: op.version || 1,
    }
    const id = await IndexedDBService.addPendingOperation(operation)
    return id
  }

  async getPendingCount(): Promise<number> {
    const operations = await IndexedDBService.getPendingOperations()
    return operations.length
  }

  async processQueue(onSuccess?: (op: PendingOperation) => void, onFailure?: (op: PendingOperation, error: Error) => void): Promise<void> {
    if (this.isProcessing) {
      return
    }
    this.isProcessing = true
    try {
      const operations = await IndexedDBService.getPendingOperations()
      const pendingOps = operations.filter((op: PendingOperation) => op.retries < this.config.maxRetries)
      for (const op of pendingOps.slice(0, this.config.batchSize)) {
        try {
          await this.executeOperation(op)
          await IndexedDBService.removePendingOperation(op.id)
          onSuccess?.(op)
        } catch (error) {
          const retryDelay = this.config.retryDelays[Math.min(op.retries, this.config.retryDelays.length - 1)]
          await IndexedDBService.updatePendingOperation(op.id, {
            retries: op.retries + 1,
            lastAttempt: new Date(),
          })
          onFailure?.(op, error as Error)
          await new Promise(resolve => setTimeout(resolve, retryDelay))
        }
      }
    } finally {
      this.isProcessing = false
    }
  }

  private async executeOperation(op: PendingOperation): Promise<void> {
    if (!this.masterUrl) {
      throw new Error('Master URL not configured')
    }
    const url = `${this.masterUrl}/api/${op.table}`
    const baseUrl = op.operation === 'INSERT' ? url : `${url}/${op.data.id}`
    const authHeaders = await getAuthHeaders()
    const options: RequestInit = {
      method: op.operation === 'INSERT' ? 'POST' : op.operation === 'UPDATE' ? 'PUT' : 'DELETE',
      headers: {
        ...authHeaders,
      },
    }
    if (op.operation !== 'DELETE') {
      options.body = JSON.stringify(op.data)
    }
    const response = await fetch(baseUrl, options)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
  }

  async flagForManualReview(op: PendingOperation): Promise<void> {
    await IndexedDBService.addConflict({
      id: crypto.randomUUID(),
      table: op.table,
      recordId: String(op.data.id || ''),
      localData: op.data,
      remoteData: {},
      localVersion: op.version,
      remoteVersion: 0,
      conflictType: 'version_mismatch',
      createdAt: new Date(),
    })
    await IndexedDBService.removePendingOperation(op.id)
  }

  startAutoProcess(callbacks: {onOnline?: () => void}): void {
    this.onOnlineCallback = callbacks.onOnline || null
    window.addEventListener('online', this.handleOnline)
  }

  stopAutoProcess(): void {
    window.removeEventListener('online', this.handleOnline)
    this.onOnlineCallback = null
  }

  private handleOnline = async (): Promise<void> => {
    if (this.onOnlineCallback) {
      this.onOnlineCallback()
    }
    await this.processQueue()
  }
}

export const SyncQueueService = new SyncQueueServiceClass()