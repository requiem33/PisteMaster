/**
 * Tests for cluster config utilities
 */

import { describe, it, expect } from 'vitest'
import type { ClusterConfig } from '../main/config/cluster'

describe('ClusterConfig', () => {
  describe('ClusterConfig interface', () => {
    it('should support single mode configuration', () => {
      const singleConfig: ClusterConfig = {
        mode: 'single',
        nodeId: 'test_node',
        udpPort: 9000,
        apiPort: 8000,
        heartbeatInterval: 5,
        heartbeatTimeout: 15,
        syncInterval: 3,
        replicaAckRequired: 1,
        ackTimeout: 5000,
        masterIp: null,
        isMaster: false,
      }

      expect(singleConfig.mode).toBe('single')
      expect(singleConfig.masterIp).toBeNull()
      expect(singleConfig.nodeId).toBe('test_node')
    })

    it('should support cluster mode configuration', () => {
      const clusterConfig: ClusterConfig = {
        mode: 'cluster',
        nodeId: 'test_node',
        masterIp: '192.168.1.100',
        udpPort: 9000,
        apiPort: 8000,
        heartbeatInterval: 5,
        heartbeatTimeout: 15,
        syncInterval: 3,
        replicaAckRequired: 1,
        ackTimeout: 5000,
        isMaster: false,
      }

      expect(clusterConfig.mode).toBe('cluster')
      expect(clusterConfig.masterIp).toBe('192.168.1.100')
    })

    it('should allow partial configuration', () => {
      const partialConfig: Partial<ClusterConfig> = {
        mode: 'cluster',
        masterIp: '192.168.1.100',
      }

      expect(partialConfig.mode).toBe('cluster')
      expect(partialConfig.masterIp).toBe('192.168.1.100')
      expect(partialConfig.nodeId).toBeUndefined()
    })
  })
})