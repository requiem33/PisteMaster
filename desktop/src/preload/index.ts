import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

interface UpdateInfo {
  version: string
}

interface OpenFileDialogOptions {
  title?: string
  filters?: { name: string; extensions: string[] }[]
  multiSelections?: boolean
}

interface SaveFileDialogOptions {
  title?: string
  defaultPath?: string
  filters?: { name: string; extensions: string[] }[]
}

interface CheckUpdateResult {
  available: boolean
  version?: string
  error?: string
}

interface ClusterConfig {
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

interface PeerInfo {
  nodeId: string
  ip: string
  port: number
  lastSeen: number
  isMaster: boolean
}

interface ClusterStatus {
  mode: 'single' | 'cluster'
  nodeId: string
  isMaster: boolean
  masterUrl: string | null
  peers: PeerInfo[]
  syncLag: number
  lastHeartbeat: number | null
  isRunning: boolean
}

interface UdpMessage {
  type: 'announce' | 'heartbeat' | 'master_announce' | 'goodbye' | 'sync_request' | 'ack'
  nodeId: string
  ip?: string
  port?: number
  timestamp: number
  isMaster?: boolean
  version?: number
  seqNum?: number
  lastSyncId?: number
  reason?: string
  syncId?: number
}

const api = {
  getAppVersion: (): Promise<string> => ipcRenderer.invoke('get-app-version'),
  getUserDataPath: (): Promise<string> => ipcRenderer.invoke('get-user-data-path'),
  getDatabasePath: (): Promise<string> => ipcRenderer.invoke('get-database-path'),
  getAppPath: (): Promise<string> => ipcRenderer.invoke('get-app-path'),

  openFileDialog: (options?: OpenFileDialogOptions): Promise<string[]> =>
    ipcRenderer.invoke('open-file-dialog', options),

  saveFileDialog: (options?: SaveFileDialogOptions): Promise<string | undefined> =>
    ipcRenderer.invoke('save-file-dialog', options),

  clearAppData: (): Promise<{ success: boolean; error?: string }> =>
    ipcRenderer.invoke('clear-app-data'),

  listDataFiles: (): Promise<string[]> => ipcRenderer.invoke('list-data-files'),

  quitAndInstall: (): void => ipcRenderer.send('quit-and-install'),

  checkForUpdates: (): Promise<CheckUpdateResult> => ipcRenderer.invoke('check-for-updates'),

  onUpdateAvailable: (callback: (info: UpdateInfo) => void): (() => void) => {
    const handler = (_event: Electron.IpcRendererEvent, info: UpdateInfo): void => {
      callback(info)
    }
    ipcRenderer.on('update-available', handler)
    return () => ipcRenderer.removeListener('update-available', handler)
  },

  cluster: {
    getConfig: (): Promise<ClusterConfig> => ipcRenderer.invoke('cluster:get-config'),
    saveConfig: (config: ClusterConfig): Promise<ClusterConfig> =>
      ipcRenderer.invoke('cluster:save-config', config),
    updateConfig: (updates: Partial<ClusterConfig>): Promise<ClusterConfig> =>
      ipcRenderer.invoke('cluster:update-config', updates),
    resetConfig: (): Promise<ClusterConfig> => ipcRenderer.invoke('cluster:reset-config'),
    isClusterMode: (): Promise<boolean> => ipcRenderer.invoke('cluster:is-cluster-mode'),
    getNodeInfo: (): Promise<{ nodeId: string; apiPort: number }> =>
      ipcRenderer.invoke('cluster:get-node-info'),
    getMasterInfo: (): Promise<{ masterIp: string | null; masterUrl: string | null }> =>
      ipcRenderer.invoke('cluster:get-master-info'),
    getStatus: (): Promise<ClusterStatus | null> => ipcRenderer.invoke('cluster:get-status'),
    getPeers: (): Promise<PeerInfo[]> => ipcRenderer.invoke('cluster:get-peers'),
    startUdp: (config: ClusterConfig): Promise<boolean> =>
      ipcRenderer.invoke('cluster:start-udp', config),
    stopUdp: (): Promise<boolean> => ipcRenderer.invoke('cluster:stop-udp'),
    restartUdp: (): Promise<boolean> => ipcRenderer.invoke('cluster:restart-udp'),
    regenerateNodeId: (): Promise<string> => ipcRenderer.invoke('cluster:regenerate-node-id'),
    sendAnnounce: (): Promise<void> => ipcRenderer.invoke('cluster:send-announce'),
    sendHeartbeat: (lastSyncId?: number): Promise<void> =>
      ipcRenderer.invoke('cluster:send-heartbeat', lastSyncId),
    sendMasterAnnounce: (): Promise<void> => ipcRenderer.invoke('cluster:send-master-announce'),
    startHeartbeat: (intervalSeconds?: number): Promise<void> =>
      ipcRenderer.invoke('cluster:start-heartbeat', intervalSeconds),
    stopHeartbeat: (): Promise<void> => ipcRenderer.invoke('cluster:stop-heartbeat'),
    onMessage: (callback: (message: UdpMessage, remoteIp: string) => void): (() => void) => {
      const channel = 'cluster:udp-message'
      const handler = (_event: Electron.IpcRendererEvent, message: UdpMessage, remoteIp: string): void => {
        callback(message, remoteIp)
      }
      ipcRenderer.on(channel, handler)
      return () => ipcRenderer.removeListener(channel, handler)
    },
    onPeerDiscovered: (callback: (peer: PeerInfo) => void): (() => void) => {
      const channel = 'cluster:peer-discovered'
      const handler = (_event: Electron.IpcRendererEvent, peer: PeerInfo): void => {
        callback(peer)
      }
      ipcRenderer.on(channel, handler)
      return () => ipcRenderer.removeListener(channel, handler)
    },
    onPeerLeft: (callback: (nodeId: string, reason?: string) => void): (() => void) => {
      const channel = 'cluster:peer-left'
      const handler = (_event: Electron.IpcRendererEvent, nodeId: string, reason?: string): void => {
        callback(nodeId, reason)
      }
      ipcRenderer.on(channel, handler)
      return () => ipcRenderer.removeListener(channel, handler)
    },
    onHeartbeat: (callback: (message: UdpMessage, remoteIp: string) => void): (() => void) => {
      const channel = 'cluster:heartbeat'
      const handler = (_event: Electron.IpcRendererEvent, message: UdpMessage, remoteIp: string): void => {
        callback(message, remoteIp)
      }
      ipcRenderer.on(channel, handler)
      return () => ipcRenderer.removeListener(channel, handler)
    },
    onMasterAnnounce: (callback: (message: UdpMessage, remoteIp: string) => void): (() => void) => {
      const channel = 'cluster:master-announce'
      const handler = (_event: Electron.IpcRendererEvent, message: UdpMessage, remoteIp: string): void => {
        callback(message, remoteIp)
      }
      ipcRenderer.on(channel, handler)
      return () => ipcRenderer.removeListener(channel, handler)
    },
    onAck: (callback: (message: UdpMessage) => void): (() => void) => {
      const channel = 'cluster:ack'
      const handler = (_event: Electron.IpcRendererEvent, message: UdpMessage): void => {
        callback(message)
      }
      ipcRenderer.on(channel, handler)
      return () => ipcRenderer.removeListener(channel, handler)
    },
  },
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', {
      ...electronAPI,
      ...api,
    })
  } catch (error) {
    console.error('Failed to expose API:', error)
  }
} else {
  // @ts-expect-error - window.electron for non-isolated context
  window.electron = {
    ...electronAPI,
    ...api,
  }
}