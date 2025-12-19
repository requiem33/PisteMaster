# PisteMaster前端架构设计文档 - MVP版本

## 🎯 项目概述

PisteMaster是一款面向击剑比赛编排的专业软件，涵盖赛事管理、实时计分、裁判调度等功能。本前端架构针对**体育赛事现场环境**
的特殊需求进行了深度优化。

## 📦 MVP技术栈选型

### 核心框架

- **Vue 3.4+** + **TypeScript 5.0+** + **Composition API**
- **Vite 5.0+** - 构建工具，支持快速开发
- **Pinia 2.1+** - 状态管理，简化数据流
- **Vue Router 4.2+** - 路由管理

### UI组件

- **Element Plus 2.3+** - 管理端UI库
- **自定义裁判端UI** - 手写大触控组件

### 数据与状态

- **IndexedDB** + **idb 8.0+** - 客户端数据库
- **localforage 1.10+** - 简化IndexedDB操作

### 表格与数据展示

- **ag-Grid Community 31.1+** - 专业级数据表格
- **vue3-virtual-scroller 2.0+** - 虚拟滚动优化

### 开发工具

- **Vitest 1.0+** - 单元测试
- **ESLint 8.56+** + **Prettier 3.1+** - 代码规范

## 🏗️ 项目架构设计

### MVP简化架构

```
pistemaster-frontend/
├── src/
│   ├── api/                    # API层（离线模式简化）
│   │   ├── offline/           # 离线API模拟
│   │   │   ├── TournamentAPI.ts
│   │   │   ├── EventAPI.ts
│   │   │   ├── FencerAPI.ts
│   │   │   ├── PoolAPI.ts
│   │   │   ├── MatchAPI.ts
│   │   │   └── index.ts
│   │   └── sync/              # 数据同步层
│   │       ├── ConflictResolver.ts
│   │       ├── IndexedDBService.ts
│   │       └── SyncManager.ts
│   ├── assets/                # 静态资源
│   ├── components/            # 业务组件（MVP核心）
│   │   ├── tournament/        # 赛事管理
│   │   │   ├── TournamentList.vue
│   │   │   ├── TournamentCreate.vue
│   │   │   └── TournamentDetail.vue
│   │   ├── event/            # 项目管理
│   │   │   ├── EventList.vue
│   │   │   ├── EventCreate.vue
│   │   │   └── EventDetail.vue
│   │   ├── fencer/           # 运动员管理
│   │   │   ├── FencerList.vue
│   │   │   ├── FencerForm.vue
│   │   │   └── FencerImport.vue
│   │   ├── pool/             # 小组赛管理
│   │   │   ├── PoolGenerator.vue
│   │   │   ├── PoolList.vue
│   │   │   └── PoolDetail.vue
│   │   ├── match/            # 比赛管理
│   │   │   ├── MatchList.vue
│   │   │   ├── MatchScoring.vue
│   │   │   └── MatchControl.vue
│   │   ├── scoring/          # 计分组件
│   │   │   ├── RefereeScoreboard.vue
│   │   │   ├── ScoreInput.vue
│   │   │   └── ScoreHistory.vue
│   │   └── shared/           # 共享组件
│   │       ├── DataTable.vue
│   │       ├── SearchFilter.vue
│   │       └── ConfirmDialog.vue
│   ├── composables/          # Composition函数
│   │   ├── useTournament.ts
│   │   ├── usePool.ts
│   │   ├── useMatch.ts
│   │   └── useSync.ts
│   ├── layouts/              # 布局组件
│   │   ├── MainLayout.vue
│   │   ├── TournamentLayout.vue
│   │   └── EventLayout.vue
│   ├── locales/              # 国际化
│   │   ├── fr.ts            # 法语（击剑官方语言）
│   │   ├── en.ts
│   │   ├── zh.ts
│   │   └── index.ts
│   ├── router/              # 路由配置
│   │   └── index.ts
│   ├── stores/              # Pinia状态（MVP核心）
│   │   ├── tournament.store.ts
│   │   ├── event.store.ts
│   │   ├── fencer.store.ts
│   │   ├── pool.store.ts
│   │   ├── match.store.ts
│   │   └── sync.store.ts    # 同步状态管理
│   ├── types/               # TypeScript类型定义
│   │   ├── models.ts        # 数据模型
│   │   ├── api.ts           # API类型
│   │   └── sync.ts          # 同步相关类型
│   ├── utils/               # 工具函数
│   │   ├── calculations/    # 计算工具
│   │   │   ├── poolRanking.ts
│   │   │   ├── bracketGenerator.ts
│   │   │   └── seedingCalculator.ts
│   │   ├── formatters/      # 格式化
│   │   ├── validators/      # 验证
│   │   └── helpers/         # 助手函数
│   ├── views/               # 页面视图（MVP核心）
│   │   ├── HomePage.vue
│   │   ├── TournamentsPage.vue
│   │   ├── TournamentPage.vue
│   │   ├── EventsPage.vue
│   │   ├── EventPage.vue
│   │   ├── ScoringPage.vue
│   │   └── SettingsPage.vue
│   └── App.vue
├── public/
└── package.json
```

## 🔄 数据同步与冲突处理策略

### 1. 离线模式数据架构

```typescript
// types/sync.ts
export interface SyncOperation {
    id: string;
    type: 'CREATE' | 'UPDATE' | 'DELETE';
    entityType: EntityType;
    entityId: string;
    data: any;
    timestamp: number;
    version: number;
    status: 'PENDING' | 'SYNCED' | 'CONFLICT' | 'ERROR';
    metadata?: {
        userId?: string;
        deviceId?: string;
        networkCondition?: string;
    };
}

export interface Conflict {
    id: string;
    operationId: string;
    localVersion: number;
    serverVersion: number;
    localData: any;
    serverData: any;
    resolvedBy?: string;
    resolvedAt?: number;
    resolution?: 'KEEP_LOCAL' | 'KEEP_SERVER' | 'MERGE';
    mergedData?: any;
}

export enum EntityType {
    TOURNAMENT = 'tournament',
    EVENT = 'event',
    FENCER = 'fencer',
    EVENT_PARTICIPANT = 'event_participant',
    POOL = 'pool',
    POOL_ASSIGNMENT = 'pool_assignment',
    POOL_BOUT = 'pool_bout',
    MATCH = 'match'
}
```

### 2. IndexedDB Schema设计

```typescript
// api/sync/IndexedDBService.ts
export class IndexedDBService {
    private db: IDBDatabase | null = null;
    private readonly DB_NAME = 'PisteMasterDB';
    private readonly DB_VERSION = 1;

    // 表定义
    private readonly STORES = {
        TOURNAMENTS: 'tournaments',
        EVENTS: 'events',
        FENCERS: 'fencers',
        EVENT_PARTICIPANTS: 'event_participants',
        POOLS: 'pools',
        POOL_ASSIGNMENTS: 'pool_assignments',
        POOL_BOUTS: 'pool_bouts',
        MATCHES: 'matches',
        SYNC_QUEUE: 'sync_queue',
        CONFLICTS: 'conflicts'
    };

    async initialize(): Promise<void> {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

            request.onerror = () => reject(request.error);

            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = (event.target as IDBOpenDBRequest).result;

                // 创建数据表
                Object.values(this.STORES).forEach(storeName => {
                    if (!db.objectStoreNames.contains(storeName)) {
                        const store = db.createObjectStore(storeName, {keyPath: 'id'});

                        // 为常用查询创建索引
                        switch (storeName) {
                            case this.STORES.TOURNAMENTS:
                                store.createIndex('by_updated', 'updated_at', {unique: false});
                                break;
                            case this.STORES.EVENTS:
                                store.createIndex('by_tournament', 'tournament_id', {unique: false});
                                store.createIndex('by_status', 'status_id', {unique: false});
                                break;
                            case this.STORES.EVENT_PARTICIPANTS:
                                store.createIndex('by_event', 'event_id', {unique: false});
                                store.createIndex('by_fencer', 'fencer_id', {unique: false});
                                break;
                            case this.STORES.POOLS:
                                store.createIndex('by_event', 'event_id', {unique: false});
                                store.createIndex('by_number', ['event_id', 'pool_number'], {unique: true});
                                break;
                            case this.STORES.POOL_BOUTS:
                                store.createIndex('by_pool', 'pool_id', {unique: false});
                                store.createIndex('by_status', 'status_id', {unique: false});
                                store.createIndex('unique_match', ['pool_id', 'fencer_a_id', 'fencer_b_id'], {unique: true});
                                break;
                            case this.STORES.SYNC_QUEUE:
                                store.createIndex('by_status', 'status', {unique: false});
                                store.createIndex('by_timestamp', 'timestamp', {unique: false});
                                break;
                        }
                    }
                });
            };
        });
    }

    // 基础CRUD操作
    async create<T extends { id: string }>(storeName: string, data: T): Promise<T> {
        return this.transaction(storeName, 'readwrite', (store) => {
            return new Promise<T>((resolve, reject) => {
                const request = store.add(data);
                request.onsuccess = () => resolve(data);
                request.onerror = () => reject(request.error);
            });
        });
    }

    async update<T extends { id: string }>(storeName: string, data: T): Promise<T> {
        return this.transaction(storeName, 'readwrite', (store) => {
            return new Promise<T>((resolve, reject) => {
                const request = store.put(data);
                request.onsuccess = () => resolve(data);
                request.onerror = () => reject(request.error);
            });
        });
    }

    // 队列管理
    async addToSyncQueue(operation: SyncOperation): Promise<void> {
        await this.create(this.STORES.SYNC_QUEUE, operation);
    }

    async getPendingOperations(limit?: number): Promise<SyncOperation[]> {
        return this.transaction(this.STORES.SYNC_QUEUE, 'readonly', (store) => {
            return new Promise((resolve, reject) => {
                const index = store.index('by_status');
                const range = IDBKeyRange.only('PENDING');
                const request = index.openCursor(range);
                const results: SyncOperation[] = [];

                request.onsuccess = (event) => {
                    const cursor = (event.target as IDBRequest).result;
                    if (cursor && (!limit || results.length < limit)) {
                        results.push(cursor.value);
                        cursor.continue();
                    } else {
                        resolve(results);
                    }
                };

                request.onerror = () => reject(request.error);
            });
        });
    }
}
```

### 3. 冲突解决策略（MVP版本）

```typescript
// api/sync/ConflictResolver.ts
export class ConflictResolver {
    // 冲突解决策略枚举
    static readonly ResolutionStrategy = {
        // 基于实体类型的策略
        ENTITY_SPECIFIC: 'entity_specific',
        // 基于操作的策略
        OPERATION_BASED: 'operation_based',
        // 最后写入获胜
        LAST_WRITE_WINS: 'last_write_wins',
        // 手动解决
        MANUAL: 'manual'
    };

    // 实体级别的冲突解决规则
    private static readonly ENTITY_RESOLUTION_RULES = {
        tournament: {
            priorityFields: ['name', 'start_date', 'status'],
            immutableFields: ['id', 'created_at'],
            mergeStrategy: 'smart'
        },
        event: {
            priorityFields: ['name', 'start_time', 'status_id'],
            immutableFields: ['id', 'tournament_id', 'created_at'],
            mergeStrategy: 'smart'
        },
        fencer: {
            priorityFields: ['first_name', 'last_name', 'country_code'],
            immutableFields: ['id', 'created_at'],
            mergeStrategy: 'smart'
        },
        event_participant: {
            priorityFields: ['seed_rank', 'is_confirmed'],
            immutableFields: ['id', 'event_id', 'fencer_id'],
            mergeStrategy: 'strict' // 严格合并，冲突时需要人工介入
        },
        pool: {
            priorityFields: ['status', 'is_completed'],
            immutableFields: ['id', 'event_id', 'pool_number'],
            mergeStrategy: 'smart'
        },
        pool_bout: {
            priorityFields: ['status_id', 'winner_id', 'fencer_a_score', 'fencer_b_score'],
            immutableFields: ['id', 'pool_id', 'fencer_a_id', 'fencer_b_id'],
            mergeStrategy: 'strict' // 比赛结果需要严格处理
        }
    };

    /**
     * 检测冲突
     */
    static detectConflict(localData: any, serverData: any, entityType: EntityType): Conflict | null {
        if (!localData || !serverData) return null;

        // 版本检查
        const localVersion = localData.version || localData.updated_at || 0;
        const serverVersion = serverData.version || serverData.updated_at || 0;

        if (localVersion === serverVersion) return null;

        // 深度比较字段差异
        const differences = this.findDifferences(localData, serverData);

        if (differences.length === 0) return null;

        // 检查是否有不可变字段被修改
        const immutableConflicts = this.checkImmutableFields(localData, serverData, entityType);

        return {
            id: `conflict_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            localVersion,
            serverVersion,
            localData,
            serverData,
            differences,
            immutableConflicts,
            entityType,
            detectedAt: Date.now()
        };
    }

    /**
     * 自动解决冲突
     */
    static async autoResolve(conflict: Conflict): Promise<ResolutionResult> {
        const entityRules = this.ENTITY_RESOLUTION_RULES[conflict.entityType];

        if (!entityRules) {
            return {
                resolved: false,
                resolution: 'MANUAL_REQUIRED',
                reason: `No resolution rules for entity type: ${conflict.entityType}`
            };
        }

        // 检查是否有不可变字段冲突
        if (conflict.immutableConflicts.length > 0) {
            return {
                resolved: false,
                resolution: 'MANUAL_REQUIRED',
                reason: 'Immutable fields modified',
                conflictingFields: conflict.immutableConflicts
            };
        }

        // 应用解决策略
        switch (entityRules.mergeStrategy) {
            case 'smart':
                return this.smartMerge(conflict, entityRules);
            case 'strict':
                return this.strictMerge(conflict);
            default:
                return this.lastWriteWins(conflict);
        }
    }

    /**
     * 智能合并策略（适用于大部分实体）
     */
    private static smartMerge(conflict: Conflict, rules: any): ResolutionResult {
        const merged = {...conflict.serverData};
        let resolutionType = 'KEEP_SERVER';

        // 根据优先级字段决定合并策略
        for (const field of conflict.differences) {
            const localValue = conflict.localData[field];
            const serverValue = conflict.serverData[field];

            // 检查是否为优先级字段
            if (rules.priorityFields.includes(field)) {
                // 对于优先级字段，总是使用服务器值（除非本地有特别理由）
                merged[field] = serverValue;
                continue;
            }

            // 对于非优先级字段，使用较新的值
            const localTimestamp = conflict.localData.updated_at || 0;
            const serverTimestamp = conflict.serverData.updated_at || 0;

            if (localTimestamp > serverTimestamp) {
                merged[field] = localValue;
                resolutionType = 'MERGE';
            } else {
                merged[field] = serverValue;
            }
        }

        return {
            resolved: true,
            resolution: resolutionType as any,
            mergedData: merged,
            notes: 'Automatically merged using smart strategy'
        };
    }

    /**
     * 严格合并策略（适用于比赛结果等关键数据）
     */
    private static strictMerge(conflict: Conflict): ResolutionResult {
        // 对于严格合并的实体，我们需要更仔细的检查

        // 特殊情况：比赛结果
        if (conflict.entityType === EntityType.POOL_BOUT ||
            conflict.entityType === EntityType.MATCH) {
            return this.resolveMatchConflict(conflict);
        }

        // 默认使用服务器数据，但记录冲突
        return {
            resolved: true,
            resolution: 'KEEP_SERVER',
            mergedData: conflict.serverData,
            notes: 'Using server data for strict entity',
            warnings: ['Conflict detected in strict entity type']
        };
    }

    /**
     * 比赛结果冲突解决
     */
    private static resolveMatchConflict(conflict: Conflict): ResolutionResult {
        const local = conflict.localData;
        const server = conflict.serverData;

        // 检查状态差异
        const localStatus = local.status_id || local.status;
        const serverStatus = server.status_id || server.status;

        // 如果一方是完成状态，另一方不是，以完成为准
        if (localStatus === 'COMPLETED' && serverStatus !== 'COMPLETED') {
            return {
                resolved: true,
                resolution: 'KEEP_LOCAL',
                mergedData: local,
                notes: 'Local match is completed while server is not'
            };
        }

        if (serverStatus === 'COMPLETED' && localStatus !== 'COMPLETED') {
            return {
                resolved: true,
                resolution: 'KEEP_SERVER',
                mergedData: server,
                notes: 'Server match is completed while local is not'
            };
        }

        // 如果双方都已完成，检查分数
        if (localStatus === 'COMPLETED' && serverStatus === 'COMPLETED') {
            // 比较分数，以较新的完成为准
            const localCompleteTime = local.actual_end_time || local.updated_at;
            const serverCompleteTime = server.actual_end_time || server.updated_at;

            if (localCompleteTime > serverCompleteTime) {
                return {
                    resolved: true,
                    resolution: 'KEEP_LOCAL',
                    mergedData: local,
                    notes: 'Local match completion is more recent'
                };
            } else {
                return {
                    resolved: true,
                    resolution: 'KEEP_SERVER',
                    mergedData: server,
                    notes: 'Server match completion is more recent'
                };
            }
        }

        // 默认使用服务器数据
        return {
            resolved: true,
            resolution: 'KEEP_SERVER',
            mergedData: server,
            notes: 'Default resolution for match conflict'
        };
    }

    /**
     * 查找数据差异
     */
    private static findDifferences(obj1: any, obj2: any): string[] {
        const differences: string[] = [];

        const allKeys = new Set([...Object.keys(obj1), ...Object.keys(obj2)]);

        for (const key of allKeys) {
            const val1 = obj1[key];
            const val2 = obj2[key];

            if (JSON.stringify(val1) !== JSON.stringify(val2)) {
                differences.push(key);
            }
        }

        return differences;
    }

    /**
     * 检查不可变字段
     */
    private static checkImmutableFields(local: any, server: any, entityType: EntityType): string[] {
        const rules = this.ENTITY_RESOLUTION_RULES[entityType];
        if (!rules?.immutableFields) return [];

        const conflicts: string[] = [];

        for (const field of rules.immutableFields) {
            if (local[field] !== undefined && server[field] !== undefined &&
                JSON.stringify(local[field]) !== JSON.stringify(server[field])) {
                conflicts.push(field);
            }
        }

        return conflicts;
    }
}
```

### 4. 同步管理器

```typescript
// api/sync/SyncManager.ts
export class SyncManager {
    private isSyncing = false;
    private syncInterval: number | null = null;
    private readonly SYNC_INTERVAL = 30000; // 30秒
    private readonly MAX_RETRIES = 3;

    constructor(
        private indexedDB: IndexedDBService,
        private conflictResolver: ConflictResolver,
        private apiClient?: any // 在线模式下的API客户端
    ) {
    }

    /**
     * 初始化同步管理器
     */
    initialize(): void {
        // 监听网络状态
        window.addEventListener('online', () => this.onNetworkOnline());
        window.addEventListener('offline', () => this.onNetworkOffline());

        // 初始化定期同步
        this.startAutoSync();
    }

    /**
     * 开始自动同步
     */
    startAutoSync(): void {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
        }

        this.syncInterval = window.setInterval(() => {
            this.syncPendingOperations();
        }, this.SYNC_INTERVAL);
    }

    /**
     * 网络恢复时的处理
     */
    private async onNetworkOnline(): Promise<void> {
        console.log('Network online, starting sync...');
        await this.syncPendingOperations(true); // 强制同步
    }

    /**
     * 网络断开时的处理
     */
    private onNetworkOffline(): void {
        console.log('Network offline, pausing sync...');
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
        }
    }

    /**
     * 同步待处理操作
     */
    async syncPendingOperations(force = false): Promise<void> {
        // 如果正在同步或离线，跳过
        if (this.isSyncing || !navigator.onLine) return;

        this.isSyncing = true;

        try {
            // 获取待处理操作
            const pendingOps = await this.indexedDB.getPendingOperations(50); // 每次同步50条

            if (pendingOps.length === 0) {
                this.isSyncing = false;
                return;
            }

            console.log(`Syncing ${pendingOps.length} operations...`);

            // 分批处理
            const batchSize = 10;
            for (let i = 0; i < pendingOps.length; i += batchSize) {
                const batch = pendingOps.slice(i, i + batchSize);
                await this.processBatch(batch);
            }

        } catch (error) {
            console.error('Sync failed:', error);
        } finally {
            this.isSyncing = false;
        }
    }

    /**
     * 处理批次操作
     */
    private async processBatch(operations: SyncOperation[]): Promise<void> {
        for (const operation of operations) {
            try {
                await this.processOperation(operation);
            } catch (error) {
                console.error(`Failed to process operation ${operation.id}:`, error);
                await this.markOperationFailed(operation, error);
            }
        }
    }

    /**
     * 处理单个操作
     */
    private async processOperation(operation: SyncOperation): Promise<void> {
        // MVP离线模式：直接标记为已同步
        if (!this.apiClient) {
            await this.markOperationSynced(operation);
            return;
        }

        // 在线模式：发送到服务器
        try {
            let response;

            switch (operation.type) {
                case 'CREATE':
                    response = await this.apiClient.create(operation.entityType, operation.data);
                    break;
                case 'UPDATE':
                    response = await this.apiClient.update(operation.entityType, operation.entityId, operation.data);
                    break;
                case 'DELETE':
                    response = await this.apiClient.delete(operation.entityType, operation.entityId);
                    break;
            }

            // 更新本地数据
            if (response) {
                await this.updateLocalData(operation.entityType, response);
            }

            await this.markOperationSynced(operation);

        } catch (error) {
            // 处理冲突
            if (this.isConflictError(error)) {
                await this.handleConflict(operation, error);
            } else {
                throw error;
            }
        }
    }

    /**
     * 处理冲突
     */
    private async handleConflict(operation: SyncOperation, error: any): Promise<void> {
        // 获取服务器最新数据
        const serverData = await this.apiClient.getById(operation.entityType, operation.entityId);

        // 获取本地数据
        const localData = await this.indexedDB.getById(operation.entityType, operation.entityId);

        // 检测冲突
        const conflict = this.conflictResolver.detectConflict(localData, serverData, operation.entityType);

        if (conflict) {
            // 尝试自动解决
            const resolution = await this.conflictResolver.autoResolve(conflict);

            if (resolution.resolved) {
                // 更新本地数据并重试操作
                const updatedData = resolution.mergedData || resolution.resolution === 'KEEP_SERVER'
                    ? serverData
                    : localData;

                await this.indexedDB.update(operation.entityType, updatedData);

                // 更新操作数据并重试
                operation.data = updatedData;
                operation.version = (operation.version || 0) + 1;

                await this.processOperation(operation);

            } else {
                // 需要手动解决
                await this.saveConflictForManualResolution(conflict, operation);
                await this.markOperationConflict(operation, conflict.id);
            }
        }
    }

    /**
     * 手动解决冲突UI组件
     */
    // components/sync/ConflictResolutionDialog.vue
    // 提供一个界面让用户手动解决冲突
}
```

## 🎨 MVP核心功能实现

### 1. 离线API模拟层

```typescript
// api/offline/TournamentAPI.ts
export class TournamentAPI {
    constructor(private indexedDB: IndexedDBService) {
    }

    async getAll(): Promise<Tournament[]> {
        return this.indexedDB.getAll('tournaments');
    }

    async getById(id: string): Promise<Tournament | null> {
        return this.indexedDB.getById('tournaments', id);
    }

    async create(data: CreateTournamentDTO): Promise<Tournament> {
        const tournament: Tournament = {
            id: uuidv4(),
            ...data,
            status_id: 'PLANNING',
            created_at: Date.now(),
            updated_at: Date.now(),
            version: 1
        };

        // 保存到IndexedDB
        await this.indexedDB.create('tournaments', tournament);

        // 添加到同步队列
        await this.addToSyncQueue('CREATE', 'tournament', tournament);

        return tournament;
    }

    async update(id: string, data: UpdateTournamentDTO): Promise<Tournament> {
        const existing = await this.getById(id);
        if (!existing) throw new Error('Tournament not found');

        const updated: Tournament = {
            ...existing,
            ...data,
            updated_at: Date.now(),
            version: (existing.version || 0) + 1
        };

        await this.indexedDB.update('tournaments', updated);

        // 添加到同步队列
        await this.addToSyncQueue('UPDATE', 'tournament', updated);

        return updated;
    }

    private async addToSyncQueue(type: 'CREATE' | 'UPDATE' | 'DELETE', entityType: string, data: any): Promise<void> {
        const operation: SyncOperation = {
            id: `op_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type,
            entityType,
            entityId: data.id,
            data,
            timestamp: Date.now(),
            version: 1,
            status: 'PENDING'
        };

        await this.indexedDB.addToSyncQueue(operation);
    }
}
```

### 2. 状态管理（Pinia）

```typescript
// stores/tournament.store.ts
export const useTournamentStore = defineStore('tournament', {
    state: () => ({
        tournaments: [] as Tournament[],
        currentTournament: null as Tournament | null,
        loading: false,
        error: null as string | null
    }),

    actions: {
        async loadTournaments() {
            this.loading = true;
            try {
                const api = new TournamentAPI(useIndexedDB());
                this.tournaments = await api.getAll();
                this.error = null;
            } catch (error) {
                this.error = 'Failed to load tournaments';
                console.error(error);
            } finally {
                this.loading = false;
            }
        },

        async createTournament(data: CreateTournamentDTO) {
            this.loading = true;
            try {
                const api = new TournamentAPI(useIndexedDB());
                const tournament = await api.create(data);
                this.tournaments.push(tournament);
                this.error = null;
                return tournament;
            } catch (error) {
                this.error = 'Failed to create tournament';
                console.error(error);
                throw error;
            } finally {
                this.loading = false;
            }
        },

        async selectTournament(id: string) {
            const api = new TournamentAPI(useIndexedDB());
            this.currentTournament = await api.getById(id);
        }
    },

    getters: {
        activeTournaments: (state) => state.tournaments.filter(t =>
            ['PLANNING', 'ONGOING'].includes(t.status_id)
        ),
        completedTournaments: (state) => state.tournaments.filter(t =>
            t.status_id === 'COMPLETED'
        )
    }
});
```

### 3. MVP核心页面流程

```vue
<!-- views/TournamentsPage.vue -->
<template>
  <div class="tournaments-page">
    <div class="page-header">
      <h1>赛事管理</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        创建新赛事
      </el-button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="进行中" name="active">
        <TournamentList :tournaments="activeTournaments"/>
      </el-tab-pane>
      <el-tab-pane label="已完成" name="completed">
        <TournamentList :tournaments="completedTournaments"/>
      </el-tab-pane>
    </el-tabs>

    <!-- 创建赛事对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建新赛事">
      <TournamentCreateForm @success="handleCreateSuccess"/>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import {computed, ref} from 'vue';
  import {useTournamentStore} from '@/stores/tournament.store';
  import TournamentList from '@/components/tournament/TournamentList.vue';
  import TournamentCreateForm from '@/components/tournament/TournamentCreateForm.vue';

  const store = useTournamentStore();
  const activeTab = ref('active');
  const showCreateDialog = ref(false);

  // 加载赛事列表
  store.loadTournaments();

  const activeTournaments = computed(() => store.activeTournaments);
  const completedTournaments = computed(() => store.completedTournaments);

  const handleCreateSuccess = (tournament: Tournament) => {
    showCreateDialog.value = false;
    // 可以跳转到赛事详情页
  };
</script>
```

## 📱 裁判端计分界面（MVP）

```vue
<!-- components/scoring/RefereeScoreboard.vue -->
<template>
  <div class="referee-scoreboard" :class="{ 'dark-mode': isDarkMode }">
    <!-- 比赛信息 -->
    <div class="match-info">
      <div class="match-code">{{ match.matchCode }}</div>
      <div class="piste">剑道: {{ match.pisteNumber }}</div>
      <div class="timer">{{ formattedTime }}</div>
    </div>

    <!-- 运动员信息 -->
    <div class="fencer-info">
      <div class="fencer left" :class="{ 'current': currentFencer === 'A' }">
        <div class="name">{{ fencerA.name }}</div>
        <div class="country">{{ fencerA.country }}</div>
        <div class="score">{{ scoreA }}</div>
      </div>

      <div class="vs">VS</div>

      <div class="fencer right" :class="{ 'current': currentFencer === 'B' }">
        <div class="name">{{ fencerB.name }}</div>
        <div class="country">{{ fencerB.country }}</div>
        <div class="score">{{ scoreB }}</div>
      </div>
    </div>

    <!-- 计分按钮 -->
    <div class="scoring-buttons">
      <button
          v-for="point in 5"
          :key="point"
          class="score-button left"
          @click="scorePoint('A')"
          :disabled="isMatchCompleted"
      >
        +{{ point }}
      </button>

      <div class="control-buttons">
        <button class="control-btn undo" @click="undo">撤销</button>
        <button class="control-btn reset" @click="reset">重置</button>
        <button class="control-btn complete" @click="completeMatch">
          完成比赛
        </button>
      </div>

      <button
          v-for="point in 5"
          :key="point"
          class="score-button right"
          @click="scorePoint('B')"
          :disabled="isMatchCompleted"
      >
        +{{ point }}
      </button>
    </div>

    <!-- 黄牌/红牌 -->
    <div class="card-controls">
      <button class="card yellow" @click="issueCard('YELLOW')">黄牌</button>
      <button class="card red" @click="issueCard('RED')">红牌</button>
    </div>

    <!-- 历史记录 -->
    <div class="score-history">
      <div v-for="(action, index) in history" :key="index" class="history-item">
        {{ formatHistoryItem(action) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import {ref, computed, onMounted} from 'vue';
  import {useMatchStore} from '@/stores/match.store';

  const props = defineProps<{
    matchId: string;
  }>();

  const store = useMatchStore();
  const currentFencer = ref<'A' | 'B' | null>(null);
  const history = ref<ScoreAction[]>([]);
  const timer = ref(0);
  const timerInterval = ref<NodeJS.Timeout | null>(null);

  // 加载比赛数据
  onMounted(async () => {
    await store.loadMatch(props.matchId);
    startTimer();
  });

  const match = computed(() => store.currentMatch);
  const fencerA = computed(() => match.value?.fencerA);
  const fencerB = computed(() => match.value?.fencerB);
  const scoreA = computed(() => match.value?.fencer_a_score || 0);
  const scoreB = computed(() => match.value?.fencer_b_score || 0);

  const isMatchCompleted = computed(() =>
      match.value?.status_id === 'COMPLETED'
  );

  const formattedTime = computed(() => {
    const minutes = Math.floor(timer.value / 60);
    const seconds = timer.value % 60;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  });

  const scorePoint = (fencer: 'A' | 'B') => {
    if (!match.value) return;

    const pointValue = 1; // 可以根据设置调整

    const action: ScoreAction = {
      type: 'SCORE',
      fencer,
      points: pointValue,
      timestamp: Date.now()
    };

    history.value.unshift(action);

    // 更新分数
    if (fencer === 'A') {
      store.updateMatchScore(props.matchId, scoreA.value + pointValue, scoreB.value);
    } else {
      store.updateMatchScore(props.matchId, scoreA.value, scoreB.value + pointValue);
    }

    // 检查比赛是否结束
    checkMatchCompletion();
  };

  const undo = () => {
    if (history.value.length === 0) return;

    const lastAction = history.value.shift();
    if (!lastAction) return;

    // 回退分数
    if (lastAction.type === 'SCORE') {
      if (lastAction.fencer === 'A') {
        store.updateMatchScore(props.matchId, scoreA.value - lastAction.points, scoreB.value);
      } else {
        store.updateMatchScore(props.matchId, scoreA.value, scoreB.value - lastAction.points);
      }
    }
  };

  const completeMatch = async () => {
    if (!match.value) return;

    const winnerId = scoreA.value > scoreB.value ? match.value.fencer_a_id : match.value.fencer_b_id;

    await store.completeMatch(props.matchId, winnerId, {
      fencer_a_score: scoreA.value,
      fencer_b_score: scoreB.value
    });

    stopTimer();
  };

  const startTimer = () => {
    if (timerInterval.value) clearInterval(timerInterval.value);

    timerInterval.value = setInterval(() => {
      timer.value++;
    }, 1000);
  };

  const stopTimer = () => {
    if (timerInterval.value) {
      clearInterval(timerInterval.value);
      timerInterval.value = null;
    }
  };

  const checkMatchCompletion = () => {
    if (!match.value) return;

    const targetScore = match.value.target_score || 5;

    if (scoreA.value >= targetScore || scoreB.value >= targetScore) {
      completeMatch();
    }
  };
</script>

<style scoped>
  .referee-scoreboard {
    background: #1a1a1a;
    color: white;
    min-height: 100vh;
    padding: 20px;
    font-family: 'Roboto', sans-serif;
  }

  .scoring-buttons {
    display: flex;
    justify-content: space-between;
    margin: 40px 0;
  }

  .score-button {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    font-size: 24px;
    font-weight: bold;
    border: none;
    cursor: pointer;
    transition: transform 0.1s;
  }

  .score-button.left {
    background: linear-gradient(135deg, #0066cc, #004499);
    color: white;
  }

  .score-button.right {
    background: linear-gradient(135deg, #cc0000, #990000);
    color: white;
  }

  .score-button:active {
    transform: scale(0.95);
  }

  .score-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .control-buttons {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .control-btn {
    padding: 15px 30px;
    border: none;
    border-radius: 10px;
    font-size: 18px;
    cursor: pointer;
  }

  .control-btn.undo {
    background: #ff9900;
    color: white;
  }

  .control-btn.reset {
    background: #666666;
    color: white;
  }

  .control-btn.complete {
    background: #00aa00;
    color: white;
  }
</style>
```

## 🚀 MVP开发路线图

### 第一阶段：基础框架（1-2周）

1. 项目初始化与架构搭建
2. IndexedDB基础服务实现
3. 核心状态管理（Pinia）
4. 基础UI组件库

### 第二阶段：核心功能（2-3周）

1. 赛事管理（创建、查看、编辑）
2. 运动员管理（添加、导入、分组）
3. 小组赛生成与显示
4. 基础计分功能

### 第三阶段：完善与测试（1-2周）

1. 冲突解决策略实现
2. 数据导出功能
3. 单元测试与集成测试
4. 性能优化

### 第四阶段：部署与验证（1周）

1. PWA打包配置
2. 离线功能测试
3. 用户手册编写
4. MVP发布

## 📋 MVP功能清单

### ✅ 核心功能

- [x] 离线数据存储（IndexedDB）
- [x] 赛事创建与管理
- [x] 运动员注册与管理
- [x] 小组赛自动分组
- [x] 小组赛对阵生成
- [x] 比赛计分与结果录入
- [x] 小组排名自动计算
- [x] 晋级名单生成

### ✅ 用户体验

- [x] 响应式设计
- [x] 裁判端大触控界面
- [x] 操作撤销/重做
- [x] 实时数据更新
- [x] 离线操作提示

### ✅ 数据管理

- [x] 本地数据持久化
- [x] 数据导入/导出（JSON）
- [x] 冲突检测基础框架
- [x] 操作日志记录

### 🔄 未来扩展（在线模式准备）

- [ ] 用户认证与权限
- [ ] 实时同步（WebSocket）
- [ ] 高级冲突解决UI
- [ ] 团队赛支持
- [ ] 高级打印功能
- [ ] 报表与统计
- [ ] 移动端应用

## 🎯 MVP技术要点

### 1. 离线优先架构

- 所有操作先在本地IndexedDB完成
- 同步操作异步进行
- 网络状态智能感知

### 2. 数据完整性

- 乐观更新与错误回滚
- 操作日志记录
- 定期数据备份

### 3. 性能优化

- 虚拟滚动大数据列表
- 懒加载图片和组件
- IndexedDB索引优化

### 4. 用户体验

- PWA支持离线使用
- 操作确认与防止误触
- 进度反馈与错误提示

## 📊 MVP数据模型简化

为MVP版本，我们简化了部分数据库设计，重点关注核心流程：

1. **Tournament** → **Event** → **Pool** → **PoolBout**
2. **Fencer** → **EventParticipant** → **PoolAssignment**
3. 移除：Team、Bout、复杂晋级树、裁判分配

这个MVP设计专注于个人赛的完整流程，为后续扩展奠定坚实基础。