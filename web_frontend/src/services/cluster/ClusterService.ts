import type {ClusterStatus, ClusterNode} from '@/types/cluster'
import {NetworkService} from '../NetworkService'
import { isElectron } from '@/utils/platform'
import { getApiBaseUrl, getAuthHeaders } from '../api'

export interface ClusterConfig {
  mode: 'single' | 'cluster'
  nodeId: string
  udpPort: number
  apiPort: number
  heartbeatInterval: number
  heartbeatTimeout: number
  syncInterval: number
  replicaAckRequired: number
  ackTimeout: number
  masterIp: string | null
  masterPort: number | null
  isMaster: boolean
}

class ClusterServiceClass {
  private masterUrl: string | null = null
  private nodeId: string | null = null
  private onMasterChangeCallbacks: Set<(newMasterUrl: string | null) => void> = new Set()
  private syncInterval: ReturnType<typeof setInterval> | null = null

  async initialize(): Promise<void> {
    this.nodeId = this.getNodeId()
    try {
      const status = await this.fetchClusterStatus()
      if (status) {
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
        `${await getApiBaseUrl()}/cluster/status/`,
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
    if (isElectron()) {
      try {
        const status = await window.electron.cluster.getStatus()
        if (status) {
          return {
            mode: status.mode,
            isMaster: status.isMaster,
            nodeId: status.nodeId,
            masterUrl: status.masterUrl,
            syncLag: status.syncLag,
            pendingAcks: 0,
            lastSyncTime: null,
            peers: (status.peers || []).map(peer => ({
              nodeId: peer.nodeId,
              role: peer.isMaster ? 'master' : 'follower',
              ipAddress: peer.ip,
              port: peer.port,
              lastHeartbeat: peer.lastSeen ? new Date(peer.lastSeen) : null,
              isHealthy: true,
              lastSyncId: 0,
            })),
          }
        }
        return null
      } catch (error) {
        console.error('Failed to get cluster status from Electron:', error)
        return null
      }
    }
    return this.fetchClusterStatus()
  }

  async getPeers(): Promise<ClusterNode[]> {
    try {
      const response = await NetworkService.fetchWithRetry<{peers: ClusterNode[]; count: number}>(
        `${await getApiBaseUrl()}/cluster/status/peers/`,
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
      const headers = await getAuthHeaders()
      const response = await fetch(`${await getApiBaseUrl()}/cluster/status/health/`, { headers })
      return response.ok
    } catch {
      return false
    }
  }

  async getConfig(): Promise<ClusterConfig | null> {
    if (!isElectron()) {
      console.warn('Cluster config is only available in desktop app')
      return null
    }

    try {
      const config = await window.electron.cluster.getConfig()
      return config
    } catch (error) {
      console.error('Failed to get cluster config:', error)
      return null
    }
  }

  async updateConfig(updates: Partial<ClusterConfig>): Promise<ClusterConfig | null> {
    if (!isElectron()) {
      console.warn('Cluster config can only be updated in desktop app')
      return null
    }

    try {
      const config = await window.electron.cluster.updateConfig(updates)

      try {
        await NetworkService.fetchWithRetry<{ mode: string }>(
          `${await getApiBaseUrl()}/cluster/status/update_config/`,
          {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              mode: config.mode,
              node_id: config.nodeId,
              udp_port: config.udpPort,
              api_port: config.apiPort,
              heartbeat_interval: config.heartbeatInterval,
              heartbeat_timeout: config.heartbeatTimeout,
              master_ip: config.masterIp,
              master_port: config.masterPort,
              is_master: config.isMaster,
            }),
          },
          3,
          1000
        )
      } catch (backendError) {
        console.warn('Failed to sync config with backend:', backendError)
      }

      return config
    } catch (error) {
      console.error('Failed to update cluster config:', error)
      return null
    }
  }

  async resetConfig(): Promise<ClusterConfig | null> {
    if (!isElectron()) {
      console.warn('Cluster config can only be reset in desktop app')
      return null
    }

    try {
      const config = await window.electron.cluster.resetConfig()

      try {
        await NetworkService.fetchWithRetry<{ mode: string }>(
          `${await getApiBaseUrl()}/cluster/status/update_config/`,
          {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              mode: config.mode,
              node_id: config.nodeId,
              udp_port: config.udpPort,
              api_port: config.apiPort,
              heartbeat_interval: config.heartbeatInterval,
              heartbeat_timeout: config.heartbeatTimeout,
              master_ip: config.masterIp,
              master_port: config.masterPort,
              is_master: config.isMaster,
            }),
          },
          3,
          1000
        )
      } catch (backendError) {
        console.warn('Failed to sync config with backend:', backendError)
      }

      return config
    } catch (error) {
      console.error('Failed to reset cluster config:', error)
      return null
    }
  }

  async regenerateNodeId(): Promise<string | null> {
    if (!isElectron()) {
      console.warn('Node ID can only be regenerated in desktop app')
      return null
    }

    try {
      const nodeId = await window.electron.cluster.regenerateNodeId()
      return nodeId
    } catch (error) {
      console.error('Failed to regenerate node ID:', error)
      return null
    }
  }

  async restartUdpService(): Promise<boolean> {
    if (!isElectron()) {
      console.warn('UDP service can only be restarted in desktop app')
      return false
    }

    try {
      const success = await window.electron.cluster.restartUdp()
      return success
    } catch (error) {
      console.error('Failed to restart UDP service:', error)
      return false
    }
  }

  async syncPull(since: number, limit = 100): Promise<{lastId: number; hasMore: boolean; changes: unknown[]}> {
    if (!this.masterUrl) {
      throw new Error('Master URL not available')
    }
    const response = await NetworkService.fetchWithRetry<{lastId: number; hasMore: boolean; changes: unknown[]}>(
      `${this.masterUrl}/api/cluster/sync/changes/?since=${since}&limit=${limit}`,
      {},
      3,
      1000
    )
    return response
  }

  async applyChanges(changes: unknown[]): Promise<{success: number; failed: number; skipped: number}> {
      const response = await NetworkService.fetchWithRetry<{success: number; failed: number; skipped: number}>(
        `${await getApiBaseUrl()}/cluster/sync/apply/`,
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
      `${this.masterUrl}/api/cluster/sync/ack/`,
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
    let lastId = 0
    let totalApplied = 0
    let hasMore = true
    while (hasMore) {
      const response = await NetworkService.fetchWithRetry<{
        last_id: number
        has_more: boolean
        changes: unknown[]
      }>(
        `${this.masterUrl}/api/cluster/sync/changes/?since=${lastId}&limit=500${tables ? '&tables=' + tables.join(',') : ''}`,
        {},
        3,
        2000,
      )
      if (response.changes.length > 0) {
        await this.applyChanges(response.changes)
        totalApplied += response.changes.length
        lastId = response.last_id
        try {
          await this.acknowledgeSync(lastId)
        } catch (ackError) {
          console.warn('ACK failed during full sync (non-fatal):', ackError)
        }
      }
      hasMore = response.has_more
      if (response.changes.length === 0) {
        hasMore = false
      }
    }
    localStorage.setItem('last_sync_id', String(lastId))
    return {totalRecords: totalApplied, totalPages: 1}
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
          try {
            await this.acknowledgeSync(newLastId)
          } catch (ackError) {
            console.warn('ACK failed (non-fatal):', ackError)
          }
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