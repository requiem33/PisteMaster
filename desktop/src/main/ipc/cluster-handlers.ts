import { ipcMain, IpcMain } from 'electron'
import {
  loadClusterConfig,
  saveClusterConfig,
  updateClusterConfig,
  resetClusterConfig,
  isClusterMode,
  getNodeInfo,
  getMasterInfo,
  generateNodeId,
  DEFAULT_CONFIG,
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
  nodeId: string
  isMaster: boolean
  masterUrl: string | null
  peers: PeerInfo[]
  syncLag: number
}

async function fetchClusterStatusFromBackend(): Promise<ClusterStatus | null> {
  try {
    const config = loadClusterConfig()
    const response = await fetch(`http://127.0.0.1:${config.apiPort}/api/cluster/status/`)
    if (!response.ok) return null
    const data = await response.json() as BackendClusterStatus
    clusterState.isMaster = data.isMaster
    clusterState.masterUrl = data.masterUrl
    return {
      mode: data.mode,
      nodeId: data.nodeId,
      isMaster: data.isMaster,
      masterUrl: data.masterUrl,
      peers: data.peers || [],
      syncLag: data.syncLag || 0,
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

  ipcMain.handle('cluster:update-config', async (_event, updates: Partial<ClusterConfig>): Promise<ClusterConfig> => {
    const currentConfig = loadClusterConfig()
    const newConfig = { ...currentConfig, ...updates }
    saveClusterConfig(newConfig)

    if (updates.mode !== undefined && updates.mode !== currentConfig.mode) {
      if (currentConfig.mode === 'cluster') {
        await udpBroadcastService.stop()
        console.log('[Cluster] UDP service stopped for mode change')
      }
      if (newConfig.mode === 'cluster') {
        await udpBroadcastService.start(newConfig)
        console.log('[Cluster] UDP service started for mode change')
      }
    }

    return newConfig
  })

  ipcMain.handle('cluster:reset-config', async (): Promise<ClusterConfig> => {
    const currentConfig = loadClusterConfig()
    const wasCluster = currentConfig.mode === 'cluster'
    
    const newConfig: ClusterConfig = {
      ...DEFAULT_CONFIG,
      nodeId: generateNodeId(),
    }
    saveClusterConfig(newConfig)

    if (wasCluster) {
      await udpBroadcastService.stop()
      console.log('[Cluster] UDP service stopped after reset')
    }

    return newConfig
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

  ipcMain.handle('cluster:get-api-url', (): string => {
    const config = loadClusterConfig()
    return `http://localhost:${config.apiPort}`
  })

  ipcMain.handle('cluster:get-status', async (): Promise<ClusterStatus | null> => {
    const config = loadClusterConfig()
    const backendStatus = await fetchClusterStatusFromBackend()
    
    if (backendStatus) {
      // Merge UDP-discovered peers with backend peers
      const udpPeers = udpBroadcastService.getPeers()
      const backendPeers = backendStatus.peers || []
      const allPeers = [...backendPeers]
      
      for (const udpPeer of udpPeers) {
        if (!allPeers.find(p => p.nodeId === udpPeer.nodeId)) {
          allPeers.push(udpPeer)
        }
      }
      
      backendStatus.peers = allPeers
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

  ipcMain.handle('cluster:restart-udp', async (): Promise<boolean> => {
    try {
      const config = loadClusterConfig()
      if (udpBroadcastService.isActive()) {
        await udpBroadcastService.stop()
      }
      if (config.mode === 'cluster') {
        await udpBroadcastService.start(config)
      }
      return true
    } catch (error) {
      console.error('[Cluster] Failed to restart UDP service:', error)
      return false
    }
  })

  ipcMain.handle('cluster:regenerate-node-id', (): string => {
    const config = loadClusterConfig()
    const newConfig = {
      ...config,
      nodeId: generateNodeId(),
    }
    saveClusterConfig(newConfig)
    return newConfig.nodeId
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