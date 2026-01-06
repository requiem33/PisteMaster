import {openDB, IDBPDatabase} from 'idb';

const DB_NAME = 'FencingAppDB';
const TOURNAMENT_STORE = 'tournaments';
const EVENT_STORE = 'events';

export const IndexedDBService = {
    /**
     * 获取数据库实例，处理版本升级逻辑
     */
    async getDB(): Promise<IDBPDatabase> {
        // 提升版本号至 2 以触发 upgrade 回调
        return openDB(DB_NAME, 5, {
            upgrade(db, oldVersion, newVersion, transaction) {
                // --- 版本 1 逻辑：创建赛事表 ---
                if (oldVersion < 1) {
                    if (!db.objectStoreNames.contains(TOURNAMENT_STORE)) {
                        db.createObjectStore(TOURNAMENT_STORE, {keyPath: 'id'});
                    }
                }

                // --- 版本 2 逻辑：创建项目表及索引 ---
                if (oldVersion < 2) {
                    if (!db.objectStoreNames.contains(EVENT_STORE)) {
                        const eventStore = db.createObjectStore(EVENT_STORE, {keyPath: 'id'});

                        // 关键：创建索引以便快速通过赛事 ID 查找其下属的所有项目
                        // 第一个参数是索引名称，第二个参数是数据对象中的键名
                        eventStore.createIndex('by_tournament', 'tournament_id');
                    }
                }

                if (oldVersion < 3) {
                    if (!db.objectStoreNames.contains('fencers')) {
                        const fencerStore = db.createObjectStore('fencers', {keyPath: 'id'});
                        // 为搜索和校验创建索引
                        fencerStore.createIndex('by_name', ['last_name', 'first_name']);
                        fencerStore.createIndex('by_fencing_id', 'fencing_id', {unique: false});
                    }
                }

                if (oldVersion < 4) {
                    if (!db.objectStoreNames.contains('event_fencers')) {
                        const store = db.createObjectStore('event_fencers', {
                            keyPath: ['event_id', 'fencer_id'] // 联合主键，防止同一个选手在一个项目里报名两次
                        });
                        // 创建索引，方便根据项目 ID 获取所有选手的 ID
                        store.createIndex('by_event', 'event_id');
                    }
                }

                if (oldVersion < 5) {
                    if (!db.objectStoreNames.contains('pools')) {
                        const poolStore = db.createObjectStore('pools', {keyPath: 'id'});
                        // 建立 event_id 索引，方便查询某个项目下的所有组
                        poolStore.createIndex('by_event', 'event_id');
                    }
                }
            },
        });
    },

    // --- 赛事 (Tournaments) 相关操作 ---

    async saveTournament(data: any) {
        const db = await this.getDB();
        // 强制脱敏，断开 Vue Proxy 引用并确保数据可克隆
        const cleanData = JSON.parse(JSON.stringify(data));
        return db.put(TOURNAMENT_STORE, cleanData);
    },

    async getAllTournaments() {
        const db = await this.getDB();
        return db.getAll(TOURNAMENT_STORE);
    },

    async getTournamentById(id: string) {
        const db = await this.getDB();
        return db.get(TOURNAMENT_STORE, id);
    },

    // --- 项目 (Events) 相关操作 ---

    /**
     * 保存或更新比赛项目
     */
    async saveEvent(data: any) {
        const db = await this.getDB();
        const cleanData = JSON.parse(JSON.stringify(data));
        return db.put(EVENT_STORE, cleanData);
    },

    /**
     * 利用索引高效获取指定赛事下的所有项目
     */
    async getEventsByTournamentId(tournamentId: string) {
        const db = await this.getDB();
        // 使用在 upgrade 中创建的 'by_tournament' 索引
        return db.getAllFromIndex(EVENT_STORE, 'by_tournament', tournamentId);
    },

    async saveEventFencerLink(link: any) {
        const db = await this.getDB();
        return db.put('event_fencers', link);
    },

    async getLinksByEvent(eventId: string) {
        const db = await this.getDB();
        return db.getAllFromIndex('event_fencers', 'by_event', eventId);
    },

    async getFencerById(id: string) {
        const db = await this.getDB();
        return db.get('fencers', id);
    },

    async getFencerByFencingId(fencingId: string) {
        const db = await this.getDB();
        return db.getFromIndex('fencers', 'by_fencing_id', fencingId);
    },

    /**
     * 保存或更新选手基本信息
     */
    async saveFencer(fencerData: any) {
        const db = await this.getDB();
        // 脱敏处理，确保是纯对象
        const cleanData = JSON.parse(JSON.stringify(fencerData));
        return db.put('fencers', cleanData);
    },

    /**
     * 根据 ID 获取特定的比赛项目 (Event)
     * 用于在关联选手后更新项目的 fencer_count
     */
    async getEventById(eventId: string) {
        const db = await this.getDB();
        return db.get(EVENT_STORE, eventId);
    },

    /**
     * 删除特定的选手-项目关联
     * @param eventId 项目ID
     * @param fencerId 选手ID
     */
    async deleteEventFencerLink(eventId: string, fencerId: string) {
        const db = await this.getDB();
        // 因为我们定义了 keyPath: ['event_id', 'fencer_id']
        // 所以删除时需要传入对应的数组键
        return db.delete('event_fencers', [eventId, fencerId]);
    },

    /**
     * 从 pools 表中根据项目 ID 查找所有分组
     */
    async getPoolsByEvent(eventId: string) {
        const db = await this.getDB();
        // 使用我们在版本 6 中创建的 'by_event' 索引
        return db.getAllFromIndex('pools', 'by_event', eventId);
    },
};