import { app } from 'electron'
import { join } from 'path'
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs'
import { hostname } from 'os'
import { randomUUID } from 'crypto'

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
}

export const DEFAULT_CONFIG: Omit<ClusterConfig, 'nodeId'> = {
  mode: 'single',
  udpPort: 9000,
  apiPort: 8000,
  heartbeatInterval: 5,
  heartbeatTimeout: 15,
  syncInterval: 3,
  replicaAckRequired: 1,
  ackTimeout: 5000,
  masterIp: null,
}

export function generateNodeId(): string {
  const host = hostname().replace(/[^a-zA-Z0-9]/g, '').slice(0, 20)
  const suffix = randomUUID().slice(0, 8)
  return `${host}_${suffix}`
}

function getConfigPath(): string {
  const userDataPath = app.getPath('userData')
  const configDir = join(userDataPath, 'config')
  if (!existsSync(configDir)) {
    mkdirSync(configDir, { recursive: true })
  }
  return join(configDir, 'cluster.json')
}

export function loadClusterConfig(): ClusterConfig {
  const configPath = getConfigPath()
  
  if (existsSync(configPath)) {
    try {
      const content = readFileSync(configPath, 'utf-8')
      const loaded = JSON.parse(content) as Partial<ClusterConfig>
      
      return {
        ...DEFAULT_CONFIG,
        ...loaded,
        nodeId: loaded.nodeId || generateNodeId(),
      }
    } catch (error) {
      console.error('Failed to load cluster config:', error)
    }
  }
  
  const newConfig: ClusterConfig = {
    ...DEFAULT_CONFIG,
    nodeId: generateNodeId(),
  }
  
  saveClusterConfig(newConfig)
  return newConfig
}

export function saveClusterConfig(config: ClusterConfig): void {
  const configPath = getConfigPath()
  try {
    writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf-8')
  } catch (error) {
    console.error('Failed to save cluster config:', error)
  }
}

export function updateClusterConfig(updates: Partial<ClusterConfig>): ClusterConfig {
  const current = loadClusterConfig()
  const updated = { ...current, ...updates }
  saveClusterConfig(updated)
  return updated
}

export function resetClusterConfig(): ClusterConfig {
  const newConfig: ClusterConfig = {
    ...DEFAULT_CONFIG,
    nodeId: generateNodeId(),
  }
  saveClusterConfig(newConfig)
  return newConfig
}

export function isClusterMode(): boolean {
  const config = loadClusterConfig()
  return config.mode === 'cluster'
}

export function getNodeInfo(): { nodeId: string; apiPort: number } {
  const config = loadClusterConfig()
  return {
    nodeId: config.nodeId,
    apiPort: config.apiPort,
  }
}

export function getMasterInfo(): { masterIp: string | null; masterUrl: string | null } {
  const config = loadClusterConfig()
  if (config.masterIp) {
    return {
      masterIp: config.masterIp,
      masterUrl: `http://${config.masterIp}:${config.apiPort}`,
    }
  }
  return {
    masterIp: null,
    masterUrl: null,
  }
}