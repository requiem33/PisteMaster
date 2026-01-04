import {IndexedDBService} from './storage/IndexedDBService';
import {v4 as uuidv4} from 'uuid'; // npm install uuid

export const DataManager = {
    async createTournament(formData: any) {
        const newTournament = {
            id: uuidv4(),
            tournament_name: formData.tournament_name,
            organizer: formData.organizer,
            location: formData.location,
            start_date: formData.date_range?.[0] || '',
            end_date: formData.date_range?.[1] || '',
            status: 'active',
            is_synced: false,
            updated_at: Date.now(),
        };

        // 1. 强制写入本地 IndexedDB (保证离线可用)
        await IndexedDBService.saveTournament(newTournament);

        // 2. 尝试在线同步 (此处留出接口，后面接 ApiService)
        try {
            if (navigator.onLine) {
                // await ApiService.post('/tournaments', newTournament);
                // newTournament.is_synced = true;
                // await IndexedDBService.saveTournament(newTournament);
            }
        } catch (e) {
            console.warn('在线同步失败，数据已保存至本地');
        }

        return newTournament;
    },

    async getTournamentList(): Promise<any[]> { // 明确指定返回 Promise<any[]>
        try {
            return await IndexedDBService.getAllTournaments() || [];
        } catch (error) {
            console.error('Fetch error:', error);
            // 关键：发生任何错误都返回一个空数组，防止前端崩溃
            return [];
        }
    },

    async getTournamentById(id: string): Promise<any | null> {
        try {
            // 1. 优先从本地 IndexedDB 查找
            const localData = await IndexedDBService.getTournamentById(id);

            // 2. 如果在线，可以尝试从后台刷新一下最新状态
            if (navigator.onLine) {
                // const remoteData = await ApiService.getTournamentById(id);
                // await IndexedDBService.saveTournament(remoteData);
                // return remoteData;
            }

            return localData || null;
        } catch (error) {
            console.error('Failed to get tournament detail:', error);
            return null;
        }
    },

    // 假设项目（Events）存储在另一个 ObjectStore
    async getEventsByTournamentId(tournamentId: string): Promise<any[]> {
        // 逻辑类似：先查本地，再查远程
        return await IndexedDBService.getEventsByTournamentId(tournamentId) || [];
    }
};