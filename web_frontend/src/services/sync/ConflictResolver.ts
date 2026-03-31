import type {ConflictItem} from '@/types/cluster'
import {IndexedDBService} from '../storage/IndexedDBService'

export type ResolutionStrategy = 'local' | 'remote' | 'newer' | 'manual'

export interface ConflictResolution {
  strategy: ResolutionStrategy
  winner: 'local' | 'remote'
  resolvedData: Record<string, unknown>
  resolvedVersion: number
}

class ConflictResolverClass {
  private manualReviewQueue: Map<string, ConflictItem> = new Map()

  resolve(localData: Record<string, unknown>, remoteData: Record<string, unknown>, localVersion: number, remoteVersion: number): ConflictResolution {
    if (localVersion > remoteVersion) {
      return {
        strategy: 'newer',
        winner: 'local',
        resolvedData: localData,
        resolvedVersion: localVersion,
      }
    }
    if (remoteVersion > localVersion) {
      return {
        strategy: 'newer',
        winner: 'remote',
        resolvedData: remoteData,
        resolvedVersion: remoteVersion,
      }
    }
    const localTimestamp = localData['last_modified_at'] as string | undefined
    const remoteTimestamp = remoteData['last_modified_at'] as string | undefined
    if (localTimestamp && remoteTimestamp) {
      if (new Date(localTimestamp) > new Date(remoteTimestamp)) {
        return {
          strategy: 'newer',
          winner: 'local',
          resolvedData: localData,
          resolvedVersion: localVersion,
        }
      }
      return {
        strategy: 'newer',
        winner: 'remote',
        resolvedData: remoteData,
        resolvedVersion: remoteVersion,
      }
    }
    return {
      strategy: 'remote',
      winner: 'remote',
      resolvedData: remoteData,
      resolvedVersion: remoteVersion,
    }
  }

  needsManualReview(recordType: string): boolean {
    const criticalTypes = ['Score', 'Ranking', 'Elimination', 'PoolResult', 'BracketResult']
    return criticalTypes.includes(recordType)
  }

  async addToManualReview(conflict: ConflictItem): Promise<void> {
    this.manualReviewQueue.set(conflict.id, conflict)
    await IndexedDBService.addConflict(conflict)
  }

  async getManualReviewQueue(): Promise<ConflictItem[]> {
    const stored = await IndexedDBService.getConflicts()
    stored.forEach(c => this.manualReviewQueue.set(c.id, c))
    return Array.from(this.manualReviewQueue.values())
  }

  async resolveManually(conflictId: string, choice: 'local' | 'remote'): Promise<void> {
    const conflict = this.manualReviewQueue.get(conflictId)
    if (!conflict) {
      throw new Error(`Conflict ${conflictId} not found`)
    }
    const resolvedData = choice === 'local' ? conflict.localData : conflict.remoteData
    const resolvedVersion = choice === 'local' ? conflict.localVersion : conflict.remoteVersion
    const tableName = conflict.table
    if (tableName === 'tournaments') {
      await IndexedDBService.saveTournament({...resolvedData, version: resolvedVersion + 1})
    } else if (tableName === 'events') {
      await IndexedDBService.saveEvent({...resolvedData, version: resolvedVersion + 1})
    } else if (tableName === 'fencers') {
      await IndexedDBService.saveFencer({...resolvedData, version: resolvedVersion + 1})
    }
    this.manualReviewQueue.delete(conflictId)
    await IndexedDBService.removeConflict(conflictId)
  }

  async resolveChange(localRecord: Record<string, unknown> | null, remoteRecord: Record<string, unknown>): Promise<{apply: boolean; data: Record<string, unknown>}> {
    if (!localRecord) {
      return {apply: true, data: remoteRecord}
    }
    const localVersion = (localRecord['version'] as number) || 1
    const remoteVersion = (remoteRecord['version'] as number) || 1
    const resolution = this.resolve(localRecord, remoteRecord, localVersion, remoteVersion)
    if (resolution.winner === 'remote') {
      return {apply: true, data: resolution.resolvedData}
    }
    return {apply: false, data: localRecord}
  }

  async resolveDelete(localRecord: Record<string, unknown> | null, recordType: string): Promise<boolean> {
    if (!localRecord) {
      return true
    }
    const localVersion = (localRecord['version'] as number) || 1
    if (localVersion > 1 && this.needsManualReview(recordType)) {
      await this.addToManualReview({
        id: crypto.randomUUID(),
        table: recordType,
        recordId: String(localRecord['id'] || ''),
        localData: localRecord,
        remoteData: {},
        localVersion,
        remoteVersion: 0,
        conflictType: 'deleted_remotely',
        createdAt: new Date(),
      })
      return false
    }
    return true
  }

  clearQueue(): void {
    this.manualReviewQueue.clear()
  }
}

export const ConflictResolver = new ConflictResolverClass()