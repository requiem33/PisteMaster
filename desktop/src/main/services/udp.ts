import { createSocket, Socket, RemoteInfo } from 'dgram'
import { EventEmitter } from 'events'
import { networkInterfaces } from 'os'
import type { ClusterConfig } from '../config/cluster'

export interface UdpMessage {
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

export interface PeerInfo {
  nodeId: string
  ip: string
  port: number
  lastSeen: number
  isMaster: boolean
}

type MessageType = UdpMessage['type']

class UdpBroadcastService extends EventEmitter {
  private socket: Socket | null = null
  private config: ClusterConfig | null = null
  private isRunning = false
  private seqNum = 0
  private peers: Map<string, PeerInfo> = new Map()
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null
  private announceRetries = 3
  private localIp: string | null = null

  async start(config: ClusterConfig): Promise<void> {
    if (this.isRunning) {
      await this.stop()
    }

    this.config = config
    this.seqNum = 0

    return new Promise((resolve, reject) => {
      this.socket = createSocket('udp4')

      this.socket.on('error', (err) => {
        console.error('[UDP] Socket error:', err)
        this.emit('error', err)
        reject(err)
      })

      this.socket.on('message', (buffer: Buffer, remoteInfo: RemoteInfo) => {
        this.handleMessage(buffer, remoteInfo)
      })

      this.socket.bind(config.udpPort, () => {
        this.socket?.setBroadcast(true)
        this.isRunning = true
        this.localIp = this.getLocalIp()
        console.log(`[UDP] Service started on port ${config.udpPort}`)
        
        this.sendAnnounce()
        resolve()
      })
    })
  }

  async stop(): Promise<void> {
    if (!this.isRunning || !this.socket) {
      return
    }

    if (this.config) {
      this.sendGoodbye()
    }

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }

    return new Promise((resolve) => {
      this.socket?.close(() => {
        this.socket = null
        this.isRunning = false
        this.peers.clear()
        console.log('[UDP] Service stopped')
        resolve()
      })
    })
  }

  private getLocalIp(): string | null {
    const interfaces = networkInterfaces()
    
    for (const name of Object.keys(interfaces)) {
      const iface = interfaces[name]
      if (!iface) continue
      
      for (const addr of iface) {
        if (addr.family === 'IPv4' && !addr.internal) {
          return addr.address
        }
      }
    }
    return null
  }

  private handleMessage(buffer: Buffer, remoteInfo: RemoteInfo): void {
    try {
      const message = JSON.parse(buffer.toString()) as UdpMessage
      
      if (message.nodeId === this.config?.nodeId) {
        return
      }

      this.emit('message', message, remoteInfo.address)

      if (message.type === 'announce') {
        this.handleAnnounce(message, remoteInfo.address)
      } else if (message.type === 'heartbeat') {
        this.handleHeartbeat(message, remoteInfo.address)
      } else if (message.type === 'master_announce') {
        this.handleMasterAnnounce(message, remoteInfo.address)
      } else if (message.type === 'goodbye') {
        this.handleGoodbye(message)
      } else if (message.type === 'ack') {
        this.emit('ack', message)
      }
    } catch (error) {
      console.error('[UDP] Failed to parse message:', error)
    }
  }

  private handleAnnounce(message: UdpMessage, remoteIp: string): void {
    if (!message.ip || !message.port) return
    
    const peerId = message.nodeId
    this.peers.set(peerId, {
      nodeId: peerId,
      ip: message.ip || remoteIp,
      port: message.port,
      lastSeen: Date.now(),
      isMaster: message.isMaster || false,
    })
    
    this.emit('peer_discovered', this.peers.get(peerId))
  }

  private handleHeartbeat(message: UdpMessage, remoteIp: string): void {
    const peerId = message.nodeId
    const existing = this.peers.get(peerId)
    
    if (existing) {
      existing.lastSeen = Date.now()
      if (message.lastSyncId !== undefined) {
        this.emit('heartbeat', message, remoteIp)
      }
    } else {
      this.peers.set(peerId, {
        nodeId: peerId,
        ip: remoteIp,
        port: message.port || this.config?.apiPort || 8000,
        lastSeen: Date.now(),
        isMaster: true,
      })
    }
    
    this.emit('heartbeat', message, remoteIp)
  }

  private handleMasterAnnounce(message: UdpMessage, remoteIp: string): void {
    const peerId = message.nodeId
    this.peers.set(peerId, {
      nodeId: peerId,
      ip: message.ip || remoteIp,
      port: message.port || this.config?.apiPort || 8000,
      lastSeen: Date.now(),
      isMaster: true,
    })
    
    this.emit('master_announce', message, remoteIp)
  }

  private handleGoodbye(message: UdpMessage): void {
    this.peers.delete(message.nodeId)
    this.emit('peer_left', message.nodeId, message.reason)
  }

  broadcast(message: UdpMessage): void {
    if (!this.socket || !this.isRunning || !this.config) {
      return
    }

    this.seqNum++
    const fullMessage = {
      ...message,
      seqNum: this.seqNum,
      timestamp: Date.now() / 1000,
    }

    const buffer = Buffer.from(JSON.stringify(fullMessage))
    this.socket.send(buffer, 0, buffer.length, this.config.udpPort, '255.255.255.255')
  }

  sendAnnounce(): void {
    if (!this.config) return

    const message: UdpMessage = {
      type: 'announce',
      nodeId: this.config.nodeId,
      ip: this.localIp || '127.0.0.1',
      port: this.config.apiPort,
      timestamp: Date.now() / 1000,
      isMaster: false,
      version: 1,
    }

    for (let i = 0; i < this.announceRetries; i++) {
      setTimeout(() => this.broadcast(message), i * 1000)
    }
  }

  sendHeartbeat(lastSyncId?: number): void {
    if (!this.config) return

    const message: UdpMessage = {
      type: 'heartbeat',
      nodeId: this.config.nodeId,
      timestamp: Date.now() / 1000,
      lastSyncId,
    }

    this.broadcast(message)
  }

  sendMasterAnnounce(): void {
    if (!this.config) return

    const message: UdpMessage = {
      type: 'master_announce',
      nodeId: this.config.nodeId,
      ip: this.localIp || '127.0.0.1',
      port: this.config.apiPort,
      timestamp: Date.now() / 1000,
    }

    this.broadcast(message)
  }

  sendGoodbye(): void {
    if (!this.config) return

    const message: UdpMessage = {
      type: 'goodbye',
      nodeId: this.config.nodeId,
      reason: 'shutdown',
      timestamp: Date.now() / 1000,
    }

    this.broadcast(message)
  }

  sendAck(nodeId: string, syncId: number): void {
    if (!this.config) return

    const message: UdpMessage = {
      type: 'ack',
      nodeId: this.config.nodeId,
      syncId,
      timestamp: Date.now() / 1000,
    }

    this.broadcast(message)
  }

  startHeartbeat(intervalSeconds: number = 5, lastSyncId?: number): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
    }

    this.heartbeatInterval = setInterval(() => {
      this.sendHeartbeat(lastSyncId)
    }, intervalSeconds * 1000)
  }

  stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  getPeers(): PeerInfo[] {
    return Array.from(this.peers.values())
  }

  getPeer(nodeId: string): PeerInfo | undefined {
    return this.peers.get(nodeId)
  }

  removePeer(nodeId: string): void {
    this.peers.delete(nodeId)
  }

  clearPeers(): void {
    this.peers.clear()
  }

  isActive(): boolean {
    return this.isRunning
  }

  getConfig(): ClusterConfig | null {
    return this.config
  }
}

export const udpBroadcastService = new UdpBroadcastService()