import { describe, it, expect } from 'vitest'
import {
  createMockClusterConfig,
  createMockClusterStatus,
  mockElectronApp,
  mockElectronIpcMain,
  mockElectronIpcRenderer,
  mockFs,
} from '../test-utils/desktop-test-utils'

describe('Desktop test utilities', () => {
  describe('createMockClusterConfig', () => {
    it('should create a default config', () => {
      const config = createMockClusterConfig()

      expect(config.mode).toBe('single')
      expect(config.udpPort).toBe(9000)
      expect(config.apiPort).toBe(8000)
      expect(config.nodeId).toBeDefined()
      expect(config.nodeId).toMatch(/^node_/)
    })

    it('should allow overriding values', () => {
      const config = createMockClusterConfig({
        mode: 'cluster',
        masterIp: '192.168.1.100',
        apiPort: 3000,
      })

      expect(config.mode).toBe('cluster')
      expect(config.masterIp).toBe('192.168.1.100')
      expect(config.apiPort).toBe(3000)
      expect(config.udpPort).toBe(9000) // Default value
    })

    it('should generate unique node IDs', () => {
      const config1 = createMockClusterConfig()
      const config2 = createMockClusterConfig()

      expect(config1.nodeId).not.toBe(config2.nodeId)
    })
  })

  describe('createMockClusterStatus', () => {
    it('should create a default status', () => {
      const status = createMockClusterStatus()

      expect(status.mode).toBe('single')
      expect(status.isMaster).toBe(false)
      expect(status.masterUrl).toBeNull()
      expect(status.peers).toEqual([])
      expect(status.syncLag).toBe(0)
      expect(status.isRunning).toBe(false)
    })

    it('should allow overriding values', () => {
      const status = createMockClusterStatus({
        mode: 'cluster',
        isMaster: true,
        masterUrl: 'http://192.168.1.100:8000',
        peers: [{ nodeId: 'peer1', ip: '192.168.1.101', port: 8000 }],
      })

      expect(status.mode).toBe('cluster')
      expect(status.isMaster).toBe(true)
      expect(status.masterUrl).toBe('http://192.168.1.100:8000')
      expect(status.peers).toHaveLength(1)
    })
  })

  describe('mockElectronApp', () => {
    it('should create mock electron app', () => {
      const app = mockElectronApp()

      expect(app.getPath).toBeDefined()
      expect(app.on).toBeDefined()
      expect(app.whenReady).toBeDefined()
      expect(app.quit).toBeDefined()
    })

    it('should return mock paths', () => {
      const app = mockElectronApp()

      const userDataPath = app.getPath('userData')
      expect(userDataPath).toBe('/mock/user/data/userData')
    })
  })

  describe('mockElectronIpcMain', () => {
    it('should create mock IPC main', () => {
      const ipcMain = mockElectronIpcMain()

      expect(ipcMain.handle).toBeDefined()
      expect(ipcMain.on).toBeDefined()
      expect(ipcMain.removeHandler).toBeDefined()
    })
  })

  describe('mockElectronIpcRenderer', () => {
    it('should create mock IPC renderer', () => {
      const ipcRenderer = mockElectronIpcRenderer()

      expect(ipcRenderer.invoke).toBeDefined()
      expect(ipcRenderer.on).toBeDefined()
      expect(ipcRenderer.send).toBeDefined()
    })
  })

  describe('mockFs', () => {
    it('should create mock file system', () => {
      const fs = mockFs()

      expect(fs.existsSync).toBeDefined()
      expect(fs.readFileSync).toBeDefined()
      expect(fs.writeFileSync).toBeDefined()
      expect(fs.mkdirSync).toBeDefined()
    })

    it('should return true for existsSync by default', () => {
      const fs = mockFs()
      const result = fs.existsSync('/some/path')

      expect(result).toBe(true)
    })

    it('should return JSON string for readFileSync by default', () => {
      const fs = mockFs()
      fs.existsSync('/config/cluster.json')
      const content = fs.readFileSync('/config/cluster.json', 'utf-8')

      expect(content).toBeDefined()
      const parsed = JSON.parse(content)
      expect(parsed.mode).toBe('single')
    })
  })
})