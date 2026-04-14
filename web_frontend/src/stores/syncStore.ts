import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {ClusterStatus, ConflictItem, NetworkStatus} from '@/types/cluster'
import {ClusterService} from '@/services/cluster/ClusterService'
import {SyncQueueService} from '@/services/sync/SyncQueueService'
import {NetworkService} from '@/services/NetworkService'
import {IndexedDBService} from '@/services/storage/IndexedDBService'

export const useSyncStore = defineStore('sync', () => {
  const isOnline = ref(NetworkService.isOnline())
  const clusterStatus = ref<ClusterStatus | null>(null)
  const pendingOperations = ref(0)
  const conflicts = ref<ConflictItem[]>([])
  const isLoading = ref(false)
  const lastSyncTime = ref<Date | null>(null)
  const lastSyncId = ref(0)
  const syncError = ref<string | null>(null)

  const isMaster = computed(() => clusterStatus.value?.isMaster ?? false)
  const isCluster = computed(() => clusterStatus.value?.mode === 'cluster')
  const masterUrl = computed(() => clusterStatus.value?.masterUrl ?? null)

  async function initialize(): Promise<void> {
    isLoading.value = true
    syncError.value = null
    try {
      await ClusterService.initialize()
      NetworkService.subscribe((status: NetworkStatus) => {
        isOnline.value = status.isOnline
      })
      const storedLastId = localStorage.getItem('last_sync_id')
      if (storedLastId) {
        lastSyncId.value = parseInt(storedLastId, 10)
      }
      await refreshStatus()
      await loadPendingCount()
      await loadConflicts()
      if (!isMaster.value && isOnline.value) {
        startSyncPolling()
      }
    } catch (error) {
      syncError.value = error instanceof Error ? error.message : 'Failed to initialize sync'
      console.error('Failed to initialize sync store:', error)
    } finally {
      isLoading.value = false
    }
  }

  async function refreshStatus(): Promise<void> {
    try {
      console.log('[SyncStore] refreshStatus: calling ClusterService.getClusterStatus()')
      const status = await ClusterService.getClusterStatus()
      console.log('[SyncStore] refreshStatus: got status:', status ? `mode=${status.mode}` : 'null')
      clusterStatus.value = status
    } catch (error) {
      console.error('[SyncStore] Failed to refresh cluster status:', error)
    }
  }

  async function loadPendingCount(): Promise<void> {
    try {
      pendingOperations.value = await SyncQueueService.getPendingCount()
    } catch (error) {
      console.error('Failed to load pending count:', error)
    }
  }

  async function loadConflicts(): Promise<void> {
    try {
      conflicts.value = await IndexedDBService.getConflicts()
    } catch (error) {
      console.error('Failed to load conflicts:', error)
    }
  }

  function startSyncPolling(intervalMs = 3000): void {
    ClusterService.startSyncPolling(intervalMs, async (changes) => {
      lastSyncTime.value = new Date()
      if (changes.length > 0) {
        const lastChange = changes[changes.length - 1] as { id: number }
        lastSyncId.value = lastChange.id
        localStorage.setItem('last_sync_id', String(lastSyncId.value))
      }
      await loadPendingCount()
    })
  }

  function stopSyncPolling(): void {
    ClusterService.stopSyncPolling()
  }

  async function processQueue(): Promise<void> {
    if (!isOnline.value) {
      syncError.value = 'Cannot process queue while offline'
      return
    }
    isLoading.value = true
    syncError.value = null
    try {
      await SyncQueueService.processQueue(
        async () => {
          await loadPendingCount()
        },
        async (_op, error) => {
          syncError.value = error.message
        }
      )
    } finally {
      isLoading.value = false
    }
  }

  async function resolveConflict(conflictId: string, choice: 'local' | 'remote'): Promise<void> {
    const {ConflictResolver} = await import('@/services/sync/ConflictResolver')
    await ConflictResolver.resolveManually(conflictId, choice)
    await loadConflicts()
  }

  async function fullSync(): Promise<void> {
    if (!isOnline.value) {
      syncError.value = 'Cannot perform full sync while offline'
      return
    }
    isLoading.value = true
    syncError.value = null
    try {
      await ClusterService.fullSync()
      lastSyncTime.value = new Date()
    } catch (error) {
      syncError.value = error instanceof Error ? error.message : 'Full sync failed'
    } finally {
      isLoading.value = false
    }
  }

  function $reset(): void {
    isOnline.value = NetworkService.isOnline()
    clusterStatus.value = null
    pendingOperations.value = 0
    conflicts.value = []
    isLoading.value = false
    lastSyncTime.value = null
    lastSyncId.value = 0
    syncError.value = null
    stopSyncPolling()
  }

  return {
    isOnline,
    clusterStatus,
    pendingOperations,
    conflicts,
    isLoading,
    lastSyncTime,
    lastSyncId,
    syncError,
    isMaster,
    isCluster,
    masterUrl,
    initialize,
    refreshStatus,
    loadPendingCount,
    loadConflicts,
    startSyncPolling,
    stopSyncPolling,
    processQueue,
    resolveConflict,
    fullSync,
    $reset,
  }
})