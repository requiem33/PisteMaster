import { ipcMain, IpcMain } from 'electron'
import {
  loadClusterConfig,
  saveClusterConfig,
  updateClusterConfig,
  resetClusterConfig,
  isClusterMode,
  getNodeInfo,
  getMasterInfo,
  type ClusterConfig,
} from '../config/cluster'
import { udpBroadcastService, type PeerInfo, type UdpMessage } from '../services/udp'

export interface ClusterStatus {
  mode: 'single' | 'cluster'
  nodeId: string
  isMaster: boolean
  masterUrl: string | null
  peers: PeerInfo[]
  syncLag: number
  lastHeartbeat: number | null
  isRunning: boolean
}

let clusterState: {
  isMaster: boolean
  masterUrl: string | null
  lastHeartbeat: number | null
  masterNodeId: string | null
} = {
  isMaster: false,
  masterUrl: null,
  lastHeartbeat: null,
  masterNodeId: null,
}

function parseClusterStatus(statusStr: string): ClusterStatus | null {
  try {
    return JSON.parse(statusStr)
  } catch {
    return null
  }
}

interface BackendClusterStatus {
  mode: 'single' | 'cluster'
  node_id: string
  is_master: boolean
  master_url: string | null
  peers: PeerInfo[]
  sync_lag: number
}

async function fetchClusterStatusFromBackend(): Promise<ClusterStatus | null> {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/cluster/status/')
    if (!response.ok) return null
    const data = await response.json() as BackendClusterStatus
    clusterState.isMaster = data.is_master
    clusterState.masterUrl = data.master_url
    return {
      mode: data.mode,
      nodeId: data.node_id,
      isMaster: data.is_master,
      masterUrl: data.master_url,
      peers: data.peers || [],
      syncLag: data.sync_lag || 0,
      lastHeartbeat: clusterState.lastHeartbeat,
      isRunning: udpBroadcastService.isActive(),
    }
  } catch {
    return null
  }
}

export function setupClusterIpcHandlers(_ipcMain: IpcMain): void {
  ipcMain.handle('cluster:get-config', (): ClusterConfig => {
    return loadClusterConfig()
  })

  ipcMain.handle('cluster:save-config', (_event, config: ClusterConfig): ClusterConfig => {
    saveClusterConfig(config)
    return config
  })

  ipcMain.handle('cluster:update-config', (_event, updates: Partial<ClusterConfig>): ClusterConfig => {
    return updateClusterConfig(updates)
  })

  ipcMain.handle('cluster:reset-config', (): ClusterConfig => {
    return resetClusterConfig()
  })

  ipcMain.handle('cluster:is-cluster-mode', (): boolean => {
    return isClusterMode()
  })

  ipcMain.handle('cluster:get-node-info', (): { nodeId: string; apiPort: number } => {
    return getNodeInfo()
  })

  ipcMain.handle('cluster:get-master-info', (): { masterIp: string | null; masterUrl: string | null } => {
    return getMasterInfo()
  })

  ipcMain.handle('cluster:get-status', async (): Promise<ClusterStatus | null> => {
    const config = loadClusterConfig()
    const backendStatus = await fetchClusterStatusFromBackend()
    
    if (backendStatus) {
      return backendStatus
    }

    return {
      mode: config.mode,
      nodeId: config.nodeId,
      isMaster: clusterState.isMaster,
      masterUrl: clusterState.masterUrl,
      peers: udpBroadcastService.getPeers(),
      syncLag: 0,
      lastHeartbeat: clusterState.lastHeartbeat,
      isRunning: udpBroadcastService.isActive(),
    }
  })

  ipcMain.handle('cluster:get-peers', (): PeerInfo[] => {
    return udpBroadcastService.getPeers()
  })

  ipcMain.handle('cluster:start-udp', async (_event, config: ClusterConfig): Promise<boolean> => {
    try {
      await udpBroadcastService.start(config)
      return true
    } catch (error) {
      console.error('[Cluster] Failed to start UDP service:', error)
      return false
    }
  })

  ipcMain.handle('cluster:stop-udp', async (): Promise<boolean> => {
    try {
      await udpBroadcastService.stop()
      return true
    } catch (error) {
      console.error('[Cluster] Failed to stop UDP service:', error)
      return false
    }
  })

  ipcMain.handle('cluster:send-announce', (): void => {
    udpBroadcastService.sendAnnounce()
  })

  ipcMain.handle('cluster:send-heartbeat', (_event, lastSyncId?: number): void => {
    udpBroadcastService.sendHeartbeat(lastSyncId)
  })

  ipcMain.handle('cluster:send-master-announce', (): void => {
    udpBroadcastService.sendMasterAnnounce()
  })

  ipcMain.handle('cluster:start-heartbeat', (_event, intervalSeconds: number = 5): void => {
    udpBroadcastService.startHeartbeat(intervalSeconds)
  })

  ipcMain.handle('cluster:stop-heartbeat', (): void => {
    udpBroadcastService.stopHeartbeat()
  })

  ipcMain.on('cluster:on-message', (_event, callback: (message: UdpMessage, remoteIp: string) => void) => {
    udpBroadcastService.on('message', callback)
  })

  ipcMain.on('cluster:on-peer-discovered', (_event, callback: (peer: PeerInfo) => void) => {
    udpBroadcastService.on('peer_discovered', callback)
  })

  ipcMain.on('cluster:on-peer-left', (_event, callback: (nodeId: string, reason?: string) => void) => {
    udpBroadcastService.on('peer_left', callback)
  })

  ipcMain.on('cluster:on-heartbeat', (_event, callback: (message: UdpMessage, remoteIp: string) => void) => {
    udpBroadcastService.on('heartbeat', callback)
  })

  ipcMain.on('cluster:on-master-announce', (_event, callback: (message: UdpMessage, remoteIp: string) => void) => {
    udpBroadcastService.on('master_announce', callback)
  })

  ipcMain.on('cluster:on-ack', (_event, callback: (message: UdpMessage) => void) => {
    udpBroadcastService.on('ack', callback)
  })
}

export function setClusterState(
  isMaster: boolean, 
  masterUrl: string | null, 
  masterNodeId: string | null
): void {
  clusterState.isMaster = isMaster
  clusterState.masterUrl = masterUrl
  clusterState.masterNodeId = masterNodeId
}

export function updateLastHeartbeat(): void {
  clusterState.lastHeartbeat = Date.now()
}

export function getClusterState(): typeof clusterState {
  return { ...clusterState }
}