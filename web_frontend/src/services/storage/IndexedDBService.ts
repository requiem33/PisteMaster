import {openDB, IDBPDatabase} from 'idb'
import type {PendingOperation, SyncQueueEntry, ConflictItem} from '@/types/cluster'
const DB_NAME = 'FencingAppDB'
const DB_VERSION = 7
const TOURNAMENT_STORE = 'tournaments'
const EVENT_STORE = 'events'
const PENDING_OPS_STORE = 'pendingOperations'
const CONFLICTS_STORE = 'conflicts'
const SYNC_QUEUE_STORE = 'syncQueue'
export const IndexedDBService = {
    async getDB(): Promise<IDBPDatabase> {
        return openDB(DB_NAME, DB_VERSION, {
            upgrade(db, oldVersion, _newVersion, transaction) {
                if (oldVersion < 1) {
                    if (!db.objectStoreNames.contains(TOURNAMENT_STORE)) {
                        db.createObjectStore(TOURNAMENT_STORE, {keyPath: 'id'})
                    }
                }
                if (oldVersion < 2) {
                    if (!db.objectStoreNames.contains(EVENT_STORE)) {
                        const eventStore = db.createObjectStore(EVENT_STORE, {keyPath: 'id'})
                        eventStore.createIndex('by_tournament', 'tournament_id')
                    }
                }
                if (oldVersion < 3) {
                    if (!db.objectStoreNames.contains('fencers')) {
                        const fencerStore = db.createObjectStore('fencers', {keyPath: 'id'})
                        fencerStore.createIndex('by_name', ['last_name', 'first_name'])
                        fencerStore.createIndex('by_fencing_id', 'fencing_id', {unique: false})
                    }
                }
                if (oldVersion < 4) {
                    if (!db.objectStoreNames.contains('event_fencers')) {
                        const store = db.createObjectStore('event_fencers', {
                            keyPath: ['event_id', 'fencer_id']
                        })
                        store.createIndex('by_event', 'event_id')
                    }
                }
                if (oldVersion < 5) {
                    if (!db.objectStoreNames.contains('pools')) {
                        const poolStore = db.createObjectStore('pools', {keyPath: 'id'})
                        poolStore.createIndex('by_event', 'event_id')
                    }
                }
                if (oldVersion < 6) {
                    const poolStore = transaction.objectStore('pools')
                    if (!poolStore.indexNames.contains('by_stage')) {
                        poolStore.createIndex('by_stage', 'stage_id')
                    }
                }
                if (oldVersion < 7) {
                    if (!db.objectStoreNames.contains(PENDING_OPS_STORE)) {
                        const pendingStore = db.createObjectStore(PENDING_OPS_STORE, {keyPath: 'id'})
                        pendingStore.createIndex('by_table', 'table')
                        pendingStore.createIndex('by_status', 'status')
                        pendingStore.createIndex('by_created', 'createdAt')
                    }
                    if (!db.objectStoreNames.contains(CONFLICTS_STORE)) {
                        const conflictStore = db.createObjectStore(CONFLICTS_STORE, {keyPath: 'id'})
                        conflictStore.createIndex('by_table', 'table')
                        conflictStore.createIndex('by_record', 'recordId')
                        conflictStore.createIndex('by_created', 'createdAt')
                    }
                    if (!db.objectStoreNames.contains(SYNC_QUEUE_STORE)) {
                        const queueStore = db.createObjectStore(SYNC_QUEUE_STORE, {keyPath: 'id'})
                        queueStore.createIndex('by_status', 'status')
                        queueStore.createIndex('by_created', 'createdAt')
                    }
                }
            },
        })
    },
    async saveTournament(data: Record<string, unknown>) {
        const db = await this.getDB()
        const cleanData = JSON.parse(JSON.stringify(data))
        return db.put(TOURNAMENT_STORE, cleanData)
    },
    async getAllTournaments() {
        const db = await this.getDB()
        return db.getAll(TOURNAMENT_STORE)
    },
    async getTournamentById(id: string) {
        const db = await this.getDB()
        return db.get(TOURNAMENT_STORE, id)
    },
    async saveEvent(data: Record<string, unknown>) {
        const db = await this.getDB()
        const cleanData = JSON.parse(JSON.stringify(data))
        return db.put(EVENT_STORE, cleanData)
    },
    async getEventsByTournamentId(tournamentId: string) {
        const db = await this.getDB()
        return db.getAllFromIndex(EVENT_STORE, 'by_tournament', tournamentId)
    },
    async saveEventFencerLink(link: Record<string, unknown>) {
        const db = await this.getDB()
        return db.put('event_fencers', link)
    },
    async getLinksByEvent(eventId: string) {
        const db = await this.getDB()
        return db.getAllFromIndex('event_fencers', 'by_event', eventId)
    },
    async getFencerById(id: string) {
        const db = await this.getDB()
        return db.get('fencers', id)
    },
    async getFencerByFencingId(fencingId: string) {
        const db = await this.getDB()
        return db.getFromIndex('fencers', 'by_fencing_id', fencingId)
    },
    async saveFencer(fencerData: Record<string, unknown>) {
        const db = await this.getDB()
        const cleanData = JSON.parse(JSON.stringify(fencerData))
        return db.put('fencers', cleanData)
    },
    async getEventById(eventId: string) {
        const db = await this.getDB()
        return db.get(EVENT_STORE, eventId)
    },
    async deleteEventFencerLink(eventId: string, fencerId: string) {
        const db = await this.getDB()
        return db.delete('event_fencers', [eventId, fencerId])
    },
    async getPoolsByEvent(eventId: string) {
        const db = await this.getDB()
        return db.getAllFromIndex('pools', 'by_event', eventId)
    },
    async deleteTournament(tournamentId: string) {
        const db = await this.getDB()
        return db.delete(TOURNAMENT_STORE, tournamentId)
    },
    async getPoolsByStage(stageId: string) {
        const db = await this.getDB()
        return db.getAllFromIndex('pools', 'by_stage', stageId)
    },
    async savePool(poolData: Record<string, unknown>) {
        const db = await this.getDB()
        const cleanData = JSON.parse(JSON.stringify(poolData))
        return db.put('pools', cleanData)
    },
    async savePools(poolsData: Record<string, unknown>[]) {
        const db = await this.getDB()
        const tx = db.transaction('pools', 'readwrite')
        for (const pool of poolsData) {
            const cleanData = JSON.parse(JSON.stringify(pool))
            await tx.store.put(cleanData)
        }
        return tx.done
    },
    async getPoolById(poolId: string) {
        const db = await this.getDB()
        return db.get('pools', poolId)
    },
    async saveFencers(fencersData: Record<string, unknown>[]) {
        const db = await this.getDB()
        const tx = db.transaction('fencers', 'readwrite')
        for (const fencer of fencersData) {
            const cleanData = JSON.parse(JSON.stringify(fencer))
            await tx.store.put(cleanData)
        }
        return tx.done
    },
    async saveEventFencerLinks(links: Record<string, unknown>[]) {
        const db = await this.getDB()
        const tx = db.transaction('event_fencers', 'readwrite')
        for (const link of links) {
            await tx.store.put(link)
        }
        return tx.done
    },
    async addPendingOperation(operation: PendingOperation): Promise<string> {
        const db = await this.getDB()
        const id = operation.id || crypto.randomUUID()
        const op = {...operation, id}
        await db.put(PENDING_OPS_STORE, op)
        return id
    },
    async getPendingOperations(): Promise<PendingOperation[]> {
        const db = await this.getDB()
        return db.getAll(PENDING_OPS_STORE)
    },
    async getPendingOperationsByTable(table: string): Promise<PendingOperation[]> {
        const db = await this.getDB()
        return db.getAllFromIndex(PENDING_OPS_STORE, 'by_table', table)
    },
    async updatePendingOperation(id: string, updates: Partial<PendingOperation>): Promise<void> {
        const db = await this.getDB()
        const op = await db.get(PENDING_OPS_STORE, id)
        if (op) {
            const updated = {...op, ...updates}
            await db.put(PENDING_OPS_STORE, updated)
        }
    },
    async removePendingOperation(id: string): Promise<void> {
        const db = await this.getDB()
        await db.delete(PENDING_OPS_STORE, id)
    },
    async clearPendingOperations(): Promise<void> {
        const db = await this.getDB()
        const tx = db.transaction(PENDING_OPS_STORE, 'readwrite')
        await tx.store.clear()
        return tx.done
    },
    async addConflict(conflict: ConflictItem): Promise<string> {
        const db = await this.getDB()
        const id = conflict.id || crypto.randomUUID()
        const item = {...conflict, id}
        await db.put(CONFLICTS_STORE, item)
        return id
    },
    async getConflicts(): Promise<ConflictItem[]> {
        const db = await this.getDB()
        return db.getAll(CONFLICTS_STORE)
    },
    async getConflictByRecord(table: string, recordId: string): Promise<ConflictItem | undefined> {
        const db = await this.getDB()
        const conflicts = await db.getAllFromIndex(CONFLICTS_STORE, 'by_record', recordId)
        return conflicts.find(c => c.table === table)
    },
    async removeConflict(id: string): Promise<void> {
        const db = await this.getDB()
        await db.delete(CONFLICTS_STORE, id)
    },
    async clearConflicts(): Promise<void> {
        const db = await this.getDB()
        const tx = db.transaction(CONFLICTS_STORE, 'readwrite')
        await tx.store.clear()
        return tx.done
    },
    async addToSyncQueue(entry: SyncQueueEntry): Promise<string> {
        const db = await this.getDB()
        const id = entry.id || crypto.randomUUID()
        const item = {...entry, id}
        await db.put(SYNC_QUEUE_STORE, item)
        return id
    },
    async getSyncQueue(status?: 'pending' | 'processing' | 'completed' | 'failed'): Promise<SyncQueueEntry[]> {
        const db = await this.getDB()
        if (status) {
            return db.getAllFromIndex(SYNC_QUEUE_STORE, 'by_status', status)
        }
        return db.getAll(SYNC_QUEUE_STORE)
    },
    async updateSyncQueueEntry(id: string, updates: Partial<SyncQueueEntry>): Promise<void> {
        const db = await this.getDB()
        const entry = await db.get(SYNC_QUEUE_STORE, id)
        if (entry) {
            const updated = {...entry, ...updates}
            await db.put(SYNC_QUEUE_STORE, updated)
        }
    },
    async removeSyncQueueEntry(id: string): Promise<void> {
        const db = await this.getDB()
        await db.delete(SYNC_QUEUE_STORE, id)
    },
    async clearSyncQueue(): Promise<void> {
        const db = await this.getDB()
        const tx = db.transaction(SYNC_QUEUE_STORE, 'readwrite')
        await tx.store.clear()
        return tx.done
    },
}