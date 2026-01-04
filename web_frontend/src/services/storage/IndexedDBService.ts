import {openDB, IDBPDatabase} from 'idb';

const DB_NAME = 'FencingAppDB';
const STORE_NAME = 'tournaments';

export const IndexedDBService = {
    async getDB(): Promise<IDBPDatabase> {
        return openDB(DB_NAME, 1, {
            upgrade(db) {
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    db.createObjectStore(STORE_NAME, {keyPath: 'id'});
                }
            },
        });
    },

    async saveTournament(data: any) {
        const db = await this.getDB();
        // 建议在这里也加一层保险，防止传入非对象
        const cleanData = JSON.parse(JSON.stringify(data));
        return db.put(STORE_NAME, cleanData);
    },

    async getAllTournaments() {
        const db = await this.getDB();
        return db.getAll(STORE_NAME);
    },

    async getTournamentById(id: string) {
        const db = await this.getDB();
        return db.get('tournaments', id);
    },

    // 如果你有 events 表
    async getEventsByTournamentId(tournamentId: string) {
        const db = await this.getDB();
        // 使用索引查询（需要在 Schema 升级时为 events 表增加 tournamentId 索引）
        return db.getAllFromIndex('events', 'tournamentId', tournamentId);
    }
};