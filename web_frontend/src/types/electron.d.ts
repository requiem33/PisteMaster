export {}

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

interface ElectronAPI {
  getAppVersion: () => Promise<string>
  getUserDataPath: () => Promise<string>
  getDatabasePath: () => Promise<string>
  getAppPath: () => Promise<string>
  openFileDialog: (options?: OpenFileDialogOptions) => Promise<string[]>
  saveFileDialog: (options?: SaveFileDialogOptions) => Promise<string | undefined>
  clearAppData: () => Promise<{ success: boolean; error?: string }>
  listDataFiles: () => Promise<string[]>
  quitAndInstall: () => void
  checkForUpdates: () => Promise<CheckUpdateResult>
  onUpdateAvailable: (callback: (info: UpdateInfo) => void) => () => void
  cluster: {
    getConfig: () => Promise<ClusterConfig>
    saveConfig: (config: ClusterConfig) => Promise<ClusterConfig>
    updateConfig: (updates: Partial<ClusterConfig>) => Promise<ClusterConfig>
    resetConfig: () => Promise<ClusterConfig>
    isClusterMode: () => Promise<boolean>
    getNodeInfo: () => Promise<{ nodeId: string; apiPort: number }>
    getMasterInfo: () => Promise<{ masterIp: string | null; masterUrl: string | null }>
    getStatus: () => Promise<ClusterStatus | null>
    getPeers: () => Promise<PeerInfo[]>
    startUdp: (config: ClusterConfig) => Promise<boolean>
    stopUdp: () => Promise<boolean>
    restartUdp: () => Promise<boolean>
    regenerateNodeId: () => Promise<string>
    sendAnnounce: () => Promise<void>
    sendHeartbeat: (lastSyncId?: number) => Promise<void>
    sendMasterAnnounce: () => Promise<void>
    startHeartbeat: (intervalSeconds?: number) => Promise<void>
    stopHeartbeat: () => Promise<void>
    onMessage: (callback: (message: UdpMessage, remoteIp: string) => void) => () => void
    onPeerDiscovered: (callback: (peer: PeerInfo) => void) => () => void
    onPeerLeft: (callback: (nodeId: string, reason?: string) => void) => () => void
    onHeartbeat: (callback: (message: UdpMessage, remoteIp: string) => void) => () => void
    onMasterAnnounce: (callback: (message: UdpMessage, remoteIp: string) => void) => () => void
    onAck: (callback: (message: UdpMessage) => void) => () => void
  }
}

declare global {
  interface Window {
    electron: ElectronAPI
  }
}