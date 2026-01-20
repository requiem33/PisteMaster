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
    },

    /**
     * 【已升级】保存分组结果，增加了 stageId
     * @param eventId
     * @param stageId - 阶段的唯一标识
     * @param poolsData
     */
    async savePools(eventId: string, stageId: string, poolsData: any[][]) {
        const db = await IndexedDBService.getDB();
        const tx = db.transaction(['pools', 'event_fencers'], 'readwrite');
        try {
            const poolStore = tx.objectStore('pools');

            // 1. 删除这个 stageId 下的旧分组，而不是整个 eventId 的
            const oldPoolsCursor = await poolStore.index('by_stage').openCursor(stageId);
            let cursor = oldPoolsCursor;
            while (cursor) {
                await cursor.delete();
                cursor = await cursor.continue();
            }

            // 2. 写入新分组，并打上 stageId 的标签
            for (let i = 0; i < poolsData.length; i++) {
                const poolId = `${stageId}_p${i + 1}`; // 用 stageId 生成唯一的 poolId
                await poolStore.put({
                    id: poolId,
                    event_id: eventId,
                    stage_id: stageId, // 👈【核心】记录阶段 ID
                    pool_number: i + 1,
                    fencer_ids: poolsData[i].map(f => f.id)
                });

                // (可选) 如果需要，可以继续更新 event_fencers 表
            }
            await tx.done;
            return true;
        } catch (e) {
            console.error('Save Pools Transaction Failed:', e);
            tx.abort();
            throw e;
        }
    },

    /**
     * 获取某个项目下的所有分组定义
     * @param eventId 项目 ID
     */
    async getPoolsByEvent(eventId: string) {
        try {
            return await IndexedDBService.getPoolsByEvent(eventId);
        } catch (error) {
            console.error('DataManager.getPoolsByEvent Error:', error);
            throw error;
        }
    },

    /**
     * 根据 ID 获取单个选手详情
     * @param fencerId 选手 ID
     */
    async getFencerById(fencerId: string) {
        try {
            return await IndexedDBService.getFencerById(fencerId);
        } catch (error) {
            console.error('DataManager.getFencerById Error:', error);
            throw error;
        }
    },

    /**
     * 【已升级】获取某个特定阶段的详细分组信息
     * @param eventId
     * @param stageId
     */
    async getPoolsDetailed(eventId: string, stageId: string) {
        try {
            // 1. 根据 stageId 从 IndexedDB 获取原始分组定义
            const poolDefinitions = await IndexedDBService.getPoolsByStage(stageId);

            if (!poolDefinitions || poolDefinitions.length === 0) {
                return null;
            }

            // 2. 排序并还原选手详情
            poolDefinitions.sort((a: any, b: any) => a.pool_number - b.pool_number);
            const detailedPools = [];
            for (const pool of poolDefinitions) {
                const fencersInPool = [];
                for (const fId of pool.fencer_ids) {
                    const detail = await this.getFencerById(fId);
                    if (detail) fencersInPool.push(detail);
                }
                detailedPools.push(fencersInPool);
            }
            return detailedPools;
        } catch (error) {
            console.error('获取详细分组失败:', error);
            return null;
        }
    },

    /**
     * 更新小组赛比分及状态
     */
    async updatePoolResults(poolId: string, results: any[][], stats: any[], isLocked: boolean) {
        const db = await IndexedDBService.getDB();
        const tx = db.transaction('pools', 'readwrite');
        const store = tx.objectStore('pools');

        try {
            const pool = await store.get(poolId);
            if (pool) {
                pool.results = JSON.parse(JSON.stringify(results)); // 脱敏保存
                pool.stats = JSON.parse(JSON.stringify(stats));
                pool.is_locked = isLocked;
                await store.put(pool);
            }
            await tx.done;
            return true;
        } catch (error) {
            console.error('更新比分失败:', error);
            return false;
        }
    },

    /**
     * 【已升级】获取某个【特定阶段】的小组赛汇总排名数据
     * @param stageId
     */
    async getEventPoolRanking(stageId: string) {
        try {
            // 1. 【核心】从 stageId 获取该阶段的所有小组记录
            const pools = await IndexedDBService.getPoolsByStage(stageId);
            if (!pools || pools.length === 0) return [];

            const rankingData = [];

            // 2. 遍历该阶段的小组，提取选手统计
            for (const pool of pools) {
                if (!pool.stats || !pool.fencer_ids) continue;

                const matchCount = pool.fencer_ids.length - 1;

                for (let i = 0; i < pool.fencer_ids.length; i++) {
                    const fencerId = pool.fencer_ids[i];
                    const fStats = pool.stats[i];

                    const fencer = await this.getFencerById(fencerId);

                    if (fencer && fStats) {
                        rankingData.push({
                            ...fencer,
                            v: fStats.V,
                            m: matchCount,
                            ts: fStats.TS,
                            tr: fStats.TR,
                            ind: fStats.Ind,
                            v_m: matchCount > 0 ? fStats.V / matchCount : 0
                        });
                    }
                }
            }
            return rankingData;
        } catch (error) {
            console.error('获取阶段汇总排名失败:', error);
            return [];
        }
    },

    /**
     * 获取淘汰赛初始对阵名单（仅限晋级选手）
     */
    async getQualifiedFencersForDE(eventId: string) {
        // 1. 获取所有选手的汇总统计（复用之前的逻辑）
        const allRanked = await this.getEventPoolRanking(eventId);

        // 2. 按照击剑规则排序：胜率 > 净胜剑 > 总得分
        const sorted = allRanked.sort((a, b) => {
            if (b.v_m !== a.v_m) return b.v_m - a.v_m;
            if (b.ind !== a.ind) return b.ind - a.ind;
            return b.ts - a.ts;
        });

        // 3. 筛选晋级选手（假设取前 80%，你可以根据需求调整或从 Event 设置中读取）
        const cutoff = Math.ceil(sorted.length * 0.8);
        return sorted.slice(0, cutoff).map((f, index) => ({
            ...f,
            seed: index + 1 // 赋予淘汰赛初始种子位
        }));
    },

    /**
     * 保存淘汰赛的完整状态
     * @param eventId
     * @param bracketData
     */
    async saveDETree(eventId: string, bracketData: any) {
        try {
            const event = await IndexedDBService.getEventById(eventId);
            if (event) {
                // 将整个对阵图数据（脱敏后）存入 event 记录中
                event.de_tree = JSON.parse(JSON.stringify(bracketData));
                await IndexedDBService.saveEvent(event);
            }
        } catch (error) {
            console.error('保存 DE 对阵图状态失败:', error);
        }
    },

    /**
     * 获取已保存的淘汰赛状态
     * @param eventId
     */
    async getDETree(eventId: string) {
        try {
            const event = await IndexedDBService.getEventById(eventId);
            return event?.de_tree || null;
        } catch (error) {
            console.error('获取 DE 对阵图状态失败:', error);
            return null;
        }
    },

    /**
     * 生成并获取最终的赛事总排名
     */
    async getFinalRanking(eventId: string) {
        // 1. 获取小组赛排名作为排序基准
        const poolRanking = await this.getEventPoolRanking(eventId);
        if (!poolRanking || poolRanking.length === 0) return [];

        const baseRankedFencers = poolRanking.sort((a, b) => {
            if (b.v_m !== a.v_m) return b.v_m - a.v_m;
            if (b.ind !== a.ind) return b.ind - a.ind;
            return b.ts - a.ts;
        }).map((f, index) => ({
            ...f,
            pool_rank: index + 1 // 附加小组赛名次
        }));

        // 2. 获取淘汰赛对阵图
        const deTree = await this.getDETree(eventId);
        if (!deTree || deTree.length === 0) {
            return baseRankedFencers.map(f => ({...f, last_round: '小组赛'}));
        }

        // 3.【关键修复】构建“选手ID -> 淘汰轮次”的映射表
        const eliminationMap = new Map<string, string>();
        const totalRounds = deTree.length;

        // 3.1【先处理特殊名次】
        const finalMatch = totalRounds > 0 ? deTree[totalRounds - 1][0] : null;
        const semiFinals = totalRounds > 1 ? deTree[totalRounds - 2] : [];

        // 处理冠亚军
        if (finalMatch && finalMatch.winnerId) {
            const winnerId = String(finalMatch.winnerId);
            const runnerUp = finalMatch.fencerA?.id === finalMatch.winnerId ? finalMatch.fencerB : finalMatch.fencerA;
            if (runnerUp) {
                eliminationMap.set(winnerId, "冠军 (Gold)");
                eliminationMap.set(String(runnerUp.id), "亚军 (Silver)");
            }
        }

        // 处理季军
        semiFinals.forEach(match => {
            if (match.winnerId) {
                const loser = match.fencerA?.id === match.winnerId ? match.fencerB : match.fencerA;
                if (loser && !eliminationMap.has(String(loser.id))) {
                    eliminationMap.set(String(loser.id), "季军 (Bronze)");
                }
            }
        });

        // 3.2【再处理其他所有轮次的淘汰者】
        deTree.forEach((round, rIdx) => {
            const roundName = `Table of ${Math.pow(2, totalRounds - rIdx)}`;
            round.forEach(match => {
                // 找出负方
                const loser = match.winnerId
                    ? (String(match.winnerId) === String(match.fencerA?.id) ? match.fencerB : match.fencerA)
                    : null;

                // 如果负方存在，并且【尚未】在特殊名次中被标记，则记录其淘汰轮次
                if (loser && !eliminationMap.has(String(loser.id))) {
                    eliminationMap.set(String(loser.id), roundName);
                }
            });
        });

        // 4. 合并数据
        const fullResults = baseRankedFencers.map(fencer => ({
            ...fencer,
            last_round: eliminationMap.get(String(fencer.id)) || '小组赛' // 默认小组赛
        }));

        // 5. 定义轮次排序权重 (索引越小，排名越高)
        const roundOrder = [
            "冠军 (Gold)",
            "亚军 (Silver)",
            "季军 (Bronze)",
            "Table of 4", // 理论上不会出现，因为半决赛负者是季军
            "Table of 8",
            "Table of 16",
            "Table of 32",
            "Table of 64",
            "小组赛",
        ];

        // 6. 最终排序
        fullResults.sort((a, b) => {
            const rankA = roundOrder.indexOf(a.last_round);
            const rankB = roundOrder.indexOf(b.last_round);

            // a. 比较淘汰轮次
            if (rankA !== rankB) {
                return rankA - rankB; // rankA=0 (冠军) > rankB=1 (亚军)，所以用 a-b
            }

            // b. 如果淘汰轮次相同，则按小组赛排名
            return a.pool_rank - b.pool_rank;
        });

        return fullResults;
    },

    /**
     * 【新增】保存当前操作的步骤索引
     */
    async saveCurrentStep(eventId: string, stepIndex: number) {
        try {
            const event = await IndexedDBService.getEventById(eventId);
            if (event) {
                event.current_step = stepIndex;
                await IndexedDBService.saveEvent(event);
            }
        } catch (error) {
            console.error('保存当前步骤失败:', error);
        }
    },

    /**
     * 【确保存在】根据ID获取单个比赛项目详情
     */
    async getEventById(eventId: string) {
        try {
            return await IndexedDBService.getEventById(eventId);
        } catch (error) {
            console.error('获取比赛项目详情失败:', error);
            return null;
        }
    },

    /**
     * 【新增】更新已有的赛事信息
     */
    async updateTournament(formData: any) {
        const tournamentToUpdate = {
            id: formData.id,
            tournament_name: formData.tournament_name,
            location: formData.location,
            start_date: formData.date_range?.[0] || '',
            end_date: formData.date_range?.[1] || '',
            updated_at: Date.now(),
        };
        // 调用 IndexedDB 的保存方法，因为 ID 相同，它会自动覆盖旧记录
        return IndexedDBService.saveTournament(tournamentToUpdate);
    },

    /**
     * 【新增】获取完整的赛事列表，包含每个赛事的项目总数和选手总数
     */
    async getTournamentListWithDetails() {
        // 1. 获取基础赛事列表
        const tournaments = await this.getTournamentList();
        if (!tournaments || tournaments.length === 0) {
            return [];
        }

        // 2. 使用 Promise.all 并行获取每个赛事的详细信息
        const detailedTournaments = await Promise.all(
            tournaments.map(async (tournament) => {
                // a. 获取该赛事下的所有项目
                const events = await this.getEventsByTournamentId(tournament.id);

                // b. 计算总选手人数
                const totalFencers = events.reduce((sum, event) => sum + (event.fencer_count || 0), 0);

                // c. 返回聚合后的新对象
                return {
                    ...tournament,
                    eventCount: events.length, // 项目总数
                    fencerCount: totalFencers, // 选手总数
                };
            })
        );

        // 3. 按更新时间排序
        detailedTournaments.sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0));

        return detailedTournaments;
    },

    /**
     * 【新增】删除一个赛事及其所有下属项目
     */
    async deleteTournament(tournamentId: string) {
        // 1. 找到该赛事下的所有项目
        const events = await this.getEventsByTournamentId(tournamentId);

        // 2. 删除每一个项目（以及与项目关联的所有数据，如选手、分组、淘汰赛等）
        for (const event of events) {
            await this.deleteEvent(event.id);
        }

        // 3. 最后删除赛事本身
        await IndexedDBService.deleteTournament(tournamentId);
        return true;
    },

    /**
     * 【新增】删除一个项目及其所有相关数据
     */
    async deleteEvent(eventId: string) {
        const db = await IndexedDBService.getDB();
        const tx = db.transaction(['events', 'event_fencers', 'pools'], 'readwrite');

        try {
            // 1. 删除项目本身
            await tx.objectStore('events').delete(eventId);

            // 2. 删除与该项目关联的 "选手报名记录"
            let cursor = await tx.objectStore('event_fencers').index('by_event').openCursor(eventId);
            while (cursor) {
                await cursor.delete();
                cursor = await cursor.continue();
            }

            // 3. 删除与该项目关联的 "小组" 记录
            cursor = await tx.objectStore('pools').index('by_event').openCursor(eventId);
            while (cursor) {
                await cursor.delete();
                cursor = await cursor.continue();
            }

            await tx.done;
            return true;
        } catch (error) {
            console.error(`删除项目 ${eventId} 失败:`, error);
            tx.abort();
            throw error;
        }
    },

    /**
     * 【新增】更新一个已有的比赛项目 (Event)
     */
    async updateEvent(eventId: string, eventData: any) {
        try {
            // 1. 获取数据库中该项目的旧数据
            const existingEvent = await IndexedDBService.getEventById(eventId);
            if (!existingEvent) {
                throw new Error(`Event with ID ${eventId} not found.`);
            }

            // 2. 将新数据与旧数据合并，确保 id 和 created_at 不变
            const updatedEventData = {
                ...existingEvent,
                ...JSON.parse(JSON.stringify(eventData)), // 用新数据覆盖旧数据
                id: eventId, // 强制确保 ID 不被意外修改
                updated_at: Date.now(), // 更新时间戳
            };

            // 3. 调用 IndexedDB 的保存方法，因为 ID 相同，它会自动覆盖
            await IndexedDBService.saveEvent(updatedEventData);
            return updatedEventData;

        } catch (error) {
            console.error(`更新项目 ${eventId} 失败:`, error);
            throw error; // 将错误抛出，以便上层可以捕获
        }
    },

    /**
     * 【核心修改】获取一个项目的“实时排名列表”中【未被淘汰】的选手
     * 简化后，它假设 live_ranking 总是存在
     */
    async getLiveFencers(eventId: string) {
        const event = await IndexedDBService.getEventById(eventId);

        // 如果 live_ranking 存在，则从中筛选、排序并返回
        if (event?.live_ranking && event.live_ranking.length > 0) {
            return event.live_ranking
                .filter((f: any) => !f.is_eliminated)
                .sort((a: any, b: any) => a.current_rank - b.current_rank);
        }

        // 如果不存在，直接返回空数组，因为正常流程下它应该已经被 FencerImport 创建了
        console.warn(`Event ${eventId} has no live_ranking yet. Returning empty array.`);
        return [];
    },

    /**
     * 更新一个项目的“实时排名列表”
     */
    async updateLiveRanking(eventId: string, rankingList: any[]) {
        try {
            const event = await IndexedDBService.getEventById(eventId);
            if (event) {
                event.live_ranking = JSON.parse(JSON.stringify(rankingList));
                await IndexedDBService.saveEvent(event);
            }
        } catch (error) {
            console.error(`更新实时排名失败 for event ${eventId}:`, error);
        }
    },

    async getPoolsByStageId(stageId: string) {
        return await IndexedDBService.getPoolsByStage(stageId);
    },
};