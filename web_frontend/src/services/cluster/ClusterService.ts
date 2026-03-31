import type {ClusterStatus, ClusterNode} from '@/types/cluster'
import {NetworkService} from '../NetworkService'

class ClusterServiceClass {
  private masterUrl: string | null = null
  private nodeId: string | null = null
  private clusterStatus: ClusterStatus | null = null
  private onMasterChangeCallbacks: Set<(newMasterUrl: string | null) => void> = new Set()
  private syncInterval: ReturnType<typeof setInterval> | null = null

  async initialize(): Promise<void> {
    this.nodeId = this.getNodeId()
    try {
      const status = await this.fetchClusterStatus()
      if (status) {
        this.clusterStatus = status
        if (status.masterUrl) {
          this.masterUrl = status.masterUrl
        } else if (status.isMaster) {
          this.masterUrl = window.location.origin
        }
      }
    } catch {
      console.warn('Failed to initialize cluster service,running in single-node mode')
    }
  }

  private getNodeId(): string {
    const storedId = localStorage.getItem('cluster_node_id')
    if (storedId) {
      return storedId
    }
    const newId = `${window.location.hostname}_${crypto.randomUUID().slice(0, 8)}`
    localStorage.setItem('cluster_node_id', newId)
    return newId
  }

  getCurrentNodeId(): string {
    return this.nodeId || this.getNodeId()
  }

  getMasterUrl(): string | null {
    return this.masterUrl
  }

  setMasterUrl(url: string | null): void {
    const oldUrl = this.masterUrl
    this.masterUrl = url
    if (oldUrl !== url) {
      this.onMasterChangeCallbacks.forEach(callback => callback(url))
    }
  }

  onMasterChange(callback: (newMasterUrl: string | null) => void): () => void {
    this.onMasterChangeCallbacks.add(callback)
    return () => {
      this.onMasterChangeCallbacks.delete(callback)
    }
  }

  async discoverMaster(): Promise<string | null> {
    try {
      const status = await this.fetchClusterStatus()
      if (status) {
        this.clusterStatus = status
        if (status.isMaster) {
          this.masterUrl = window.location.origin
        } else if (status.masterUrl) {
          this.masterUrl = status.masterUrl
        }
        return this.masterUrl
      }
    } catch {
      console.warn('Failed to discover master node')
    }
    return null
  }

  private async fetchClusterStatus(): Promise<ClusterStatus | null> {
    try {
      const response = await NetworkService.fetchWithRetry<ClusterStatus>(
        '/api/cluster/status/',
        {},
        2,
        500
      )
      return response
    } catch {
      return null
    }
  }

  async getClusterStatus(): Promise<ClusterStatus | null> {
    return this.fetchClusterStatus()
  }

  async getPeers(): Promise<ClusterNode[]> {
    try {
      const response = await NetworkService.fetchWithRetry<{peers: ClusterNode[]; count: number}>(
        '/api/cluster/status/peers/',
        {},
        2,
        500
      )
      return response.peers
    } catch {
      return []
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch('/api/cluster/status/health/')
      return response.ok
    } catch {
      return false
    }
  }

  async syncPull(since: number, limit = 100): Promise<{lastId: number; hasMore: boolean; changes: unknown[]}> {
    if (!this.masterUrl) {
      throw new Error('Master URL not available')
    }
    const response = await NetworkService.fetchWithRetry<{lastId: number; hasMore: boolean; changes: unknown[]}>(
      `${this.masterUrl}/api/sync/changes/?since=${since}&limit=${limit}`,
      {},
      3,
      1000
    )
    return response
  }

  async applyChanges(changes: unknown[]): Promise<{success: number; failed: number; skipped: number}> {
    if (!this.masterUrl) {
      throw new Error('Master URL not available')
    }
    const response = await NetworkService.fetchWithRetry<{success: number; failed: number; skipped: number}>(
      `${this.masterUrl}/api/sync/apply/`,
      {
        method: 'POST',
        body: JSON.stringify({changes}),
      },
      3,
      1000
    )
    return response
  }

  async acknowledgeSync(syncId: number): Promise<void> {
    if (!this.masterUrl) {
      throw new Error('Master URL not available')
    }
    await NetworkService.fetchWithRetry(
      `${this.masterUrl}/api/sync/ack/`,
      {
        method: 'POST',
        body: JSON.stringify({
          node_id: this.getCurrentNodeId(),
          sync_id: syncId,
        }),
      },
      3,
      500
    )
  }

  async fullSync(tables?: string[]): Promise<{totalRecords: number; totalPages: number}> {
    if (!this.masterUrl) {
      throw new Error('Master URL not available')
    }
    const params = new URLSearchParams()
    if (tables && tables.length > 0) {
      params.set('tables', tables.join(','))
    }
    const response = await NetworkService.fetchWithRetry<{totalRecords: number; totalPages: number}>(
      `${this.masterUrl}/api/sync/full/?${params.toString()}`,
      {},
      3,
      2000
    )
    return response
  }

  startSyncPolling(intervalMs = 3000, onSync?: (changes: unknown[]) => void): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval)
    }
    this.syncInterval = setInterval(async () => {
      try {
        const lastSyncId = parseInt(localStorage.getItem('last_sync_id') || '0', 10)
        const result = await this.syncPull(lastSyncId)
        if (result.changes.length > 0) {
          await this.applyChanges(result.changes)
          const newLastId = result.lastId
          localStorage.setItem('last_sync_id', String(newLastId))
          onSync?.(result.changes)
        }
      } catch (error) {
        console.error('Sync polling failed:', error)
      }
    }, intervalMs)
  }

  stopSyncPolling(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval)
      this.syncInterval = null
    }
  }

  destroy(): void {
    this.stopSyncPolling()
    this.onMasterChangeCallbacks.clear()
  }
}

export const ClusterService = new ClusterServiceClass()