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

    async createEvent(eventData: any) {
        const newEvent = {
            ...JSON.parse(JSON.stringify(eventData)), // 脱敏 Vue Proxy
            id: uuidv4(),
            status: '正在报名', // 初始状态名，实际开发建议用状态码
            fencer_count: 0,
            is_synced: false,
            updated_at: Date.now()
        };

        // 1. 存入本地
        await IndexedDBService.saveEvent(newEvent);

        // 2. 尝试在线同步 (此处留空给后端对接)
        if (navigator.onLine) {
            // ApiService.post('/events', newEvent)...
        }

        return newEvent;
    },

    async getEventsByTournamentId(tournamentId: string): Promise<any[]> {
        return (await IndexedDBService.getEventsByTournamentId(tournamentId)) || [];
    },

    async saveFencers(fencerList: any[]) {
        const timestamp = Date.now();
        const preparedFencers = [];

        for (const f of fencerList) {
            // 1. 寻找唯一标识（假设以 fencing_id 或证件号为准）
            let existingFencer = null;
            if (f.fencing_id) {
                existingFencer = await IndexedDBService.getFencerByFencingId(f.fencing_id);
            }

            const fencerData = {
                ...JSON.parse(JSON.stringify(f)),
                // 如果库里已有，延用旧 ID；否则才生成新 UUID
                id: existingFencer ? existingFencer.id : (f.id || uuidv4()),
                display_name: `${f.last_name}${f.first_name}`,
                updated_at: timestamp,
                created_at: existingFencer ? existingFencer.created_at : timestamp,
                is_synced: false
            };

            await IndexedDBService.saveFencer(fencerData);
            preparedFencers.push(fencerData);
        }
        return preparedFencers;
    },

    async linkFencersToEvent(eventId: string, fencerIds: string[]) {
        const timestamp = Date.now();

        // 准备关联数据
        const links = fencerIds.map(fId => ({
            event_id: eventId,
            fencer_id: fId,
            created_at: timestamp,
            is_synced: false // 标记该“报名关系”尚未同步到后端
        }));

        try {
            // 1. 本地持久化关联关系
            for (const link of links) {
                await IndexedDBService.saveEventFencerLink(link);
            }

            // 2. 更新 Event 表中的 fencer_count (可选，为了 Dashboard 显示方便)
            const allLinks = await IndexedDBService.getLinksByEvent(eventId);
            const event = await IndexedDBService.getEventById(eventId);
            if (event) {
                event.fencer_count = allLinks.length; // 直接使用最新统计值，更安全
                await IndexedDBService.saveEvent(event);
            }

            // 3. 在线模式下向 API 发送关联请求
            if (navigator.onLine) {
                // ApiService.linkFencers(eventId, fencerIds);
            }

            return true;
        } catch (error) {
            console.error('Link Fencers Error:', error);
            throw error;
        }
    },

    /**
     * 获取某个项目下的所有选手详情
     */
    async getFencersByEvent(eventId: string) {
        // 1. 从中间表拿到所有关联记录
        const links = await IndexedDBService.getLinksByEvent(eventId);
        const fencerIds = links.map(l => l.fencer_id);

        // 2. 根据 ID 列表去 fencers 表查出完整信息
        const fencerDetails = [];
        for (const id of fencerIds) {
            const detail = await IndexedDBService.getFencerById(id);
            if (detail) fencerDetails.push(detail);
        }

        return fencerDetails;
    },

    async syncEventFencers(eventId: string, currentFencerIds: string[]) {
        try {
            // 1. 获取数据库中该项目原有的所有关联
            const oldLinks = await IndexedDBService.getLinksByEvent(eventId);
            const oldFencerIds = oldLinks.map(link => link.fencer_id);

            // 2. 找出需要删除的（在旧名单里，但不在新名单里）
            const idsToDelete = oldFencerIds.filter(id => !currentFencerIds.includes(id));

            // 3. 执行删除操作
            for (const fencerId of idsToDelete) {
                await IndexedDBService.deleteEventFencerLink(eventId, fencerId);
            }

            // 4. 执行新增/更新操作（即你之前的逻辑）
            const timestamp = Date.now();
            for (const fId of currentFencerIds) {
                await IndexedDBService.saveEventFencerLink({
                    event_id: eventId,
                    fencer_id: fId,
                    updated_at: timestamp,
                    is_synced: false
                });
            }

            // 5. 更新项目的选手计数
            const event = await IndexedDBService.getEventById(eventId);
            if (event) {
                event.fencer_count = currentFencerIds.length;
                await IndexedDBService.saveEvent(event);
            }

            return true;
        } catch (error) {
            console.error('Sync Fencers Error:', error);
            throw error;
        }
    }
};