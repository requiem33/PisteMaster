export interface PendingOperation {
  id: string
  operation: 'INSERT' | 'UPDATE' | 'DELETE'
  table: string
  data: Record<string, unknown>
  version: number
  retries: number
  lastAttempt: Date | null
  createdAt: Date
}

export interface SyncQueueEntry {
  id: string
  operations: PendingOperation[]
  status: 'pending' | 'processing' | 'completed' | 'failed'
  createdAt: Date
  updatedAt: Date
}

export interface ConflictItem {
  id: string
  table: string
  recordId: string
  localData: Record<string, unknown>
  remoteData: Record<string, unknown>
  localVersion: number
  remoteVersion: number
  conflictType: 'version_mismatch' | 'deleted_locally' | 'deleted_remotely'
  createdAt: Date
}

export interface NetworkStatus {
  isOnline: boolean
  lastOnline: Date | null
  lastOffline: Date | null
  latency: number | null
}

export interface ClusterNode {
  nodeId: string
  role: 'master' | 'follower' | 'single'
  ipAddress: string | null
  port: number | null
  lastHeartbeat: Date | null
  isHealthy: boolean
  lastSyncId: number
}

export interface ClusterStatus {
  mode: 'single' | 'cluster'
  isMaster: boolean
  nodeId: string
  masterUrl: string | null
  syncLag: number
  pendingAcks: number
  lastSyncTime: Date | null
  peers: ClusterNode[]
}