/**
 * Desktop test utilities
 * Provides helpers for testing Electron desktop app
 */

import { vi } from 'vitest'

export interface MockClusterConfig {
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
  isMaster: boolean
}

export function createMockClusterConfig(
  overrides: Partial<MockClusterConfig> = {}
): MockClusterConfig {
  return {
    mode: 'single',
    nodeId: `node_${Math.random().toString(36).slice(2, 10)}`,
    udpPort: 9000,
    apiPort: 8000,
    heartbeatInterval: 5,
    heartbeatTimeout: 15,
    syncInterval: 3,
    replicaAckRequired: 1,
    ackTimeout: 5000,
    masterIp: null,
    isMaster: false,
    ...overrides,
  }
}

export function createMockClusterStatus(overrides: Partial<any> = {}) {
  return {
    mode: 'single' as const,
    nodeId: `node_${Math.random().toString(36).slice(2, 10)}`,
    isMaster: false,
    masterUrl: null,
    peers: [],
    syncLag: 0,
    lastHeartbeat: null,
    isRunning: false,
    ...overrides,
  }
}

export function mockElectronApp() {
  return {
    getPath: vi.fn((path: string) => `/mock/user/data/${path}`),
    getPathUserData: vi.fn(() => '/mock/user/data'),
    on: vi.fn(),
    whenReady: vi.fn(() => Promise.resolve()),
    quit: vi.fn(),
  }
}

export function mockElectronIpcMain() {
  return {
    handle: vi.fn(),
    on: vi.fn(),
    removeHandler: vi.fn(),
  }
}

export function mockElectronIpcRenderer() {
  return {
    invoke: vi.fn(),
    on: vi.fn(),
    send: vi.fn(),
  }
}

export function mockFs() {
  return {
    existsSync: vi.fn(() => true),
    readFileSync: vi.fn(() => JSON.stringify(createMockClusterConfig())),
    writeFileSync: vi.fn(),
    mkdirSync: vi.fn(),
  }
}