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
        return openDB(DB_NAME, 2, {
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
    }
};