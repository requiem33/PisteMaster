import {IndexedDBService} from './storage/IndexedDBService';
import {ElMessage} from 'element-plus';
import {v4 as uuidv4} from 'uuid';
import type {Tournament} from '@/types/tournament.ts';
import {getCsrfToken} from '@/utils/csrf.ts';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

function getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };
    const csrfToken = getCsrfToken();
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }
    return headers;
}

export const DataManager = {
    async createTournament(formData: any): Promise<any | null> {
        try {
            // 【核心改造】在这里重塑数据
            const payload = {
                tournament_name: formData.tournament_name,
                organizer: formData.organizer,
                location: formData.location,
                start_date: formData.date_range ? formData.date_range[0] : null,
                end_date: formData.date_range ? formData.date_range[1] : null,
            };

            const response = await fetch(`${API_BASE_URL}/tournaments/`, {
                method: 'POST',
                headers: getHeaders(),
                credentials: 'include',
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json();
                // 现在的错误信息会非常具体，比如 "end_date: ['结束日期不能早于开始日期']"
                const errorMessage = Object.values(errorData).flat().join(' ');
                ElMessage.error(`创建失败: ${errorMessage}`);
                console.error("后端验证错误:", errorData);
                return null;
            }

            const newTournament = await response.json();
            ElMessage.success('赛事已成功创建！');
            return newTournament;

        } catch (error) {
            console.error('网络或请求错误:', error);
            ElMessage.error('无法连接到后端服务。');
            return null;
        }
    },

    async getTournamentList(): Promise<any[]> {
        try {
            const response = await fetch(`${API_BASE_URL}/tournaments/`);
            if (!response.ok) throw new Error('Failed to fetch tournaments');
            const data = await response.json();
            return data.results || data;
        } catch (error) {
            console.error('Fetch error:', error);
            return [];
        }
    },

    async getTournamentById(id: string): Promise<any | null> {
        try {
            const response = await fetch(`${API_BASE_URL}/tournaments/${id}/`);
            if (!response.ok) throw new Error('Failed to fetch tournament');
            return await response.json();
        } catch (error) {
            console.error('Failed to get tournament detail:', error);
            return null;
        }
    },

    async updateTournament(formData: any) {
        try {
            const payload = {
                tournament_name: formData.tournament_name,
                organizer: formData.organizer,
                location: formData.location,
                start_date: formData.date_range ? formData.date_range[0] : formData.start_date,
                end_date: formData.date_range ? formData.date_range[1] : formData.end_date,
            };

            const response = await fetch(`${API_BASE_URL}/tournaments/${formData.id}/`, {
                method: 'PUT',
                headers: getHeaders(),
                credentials: 'include',
                body: JSON.stringify(payload),
            });
            if (!response.ok) throw new Error('Failed to update tournament');
            return await response.json();
        } catch (error) {
            console.error('Update tournament error:', error);
            throw error;
        }
    },

    async deleteTournament(tournamentId: string) {
        try {
            const response = await fetch(`${API_BASE_URL}/tournaments/${tournamentId}/`, {
                method: 'DELETE',
                headers: getHeaders(),
                credentials: 'include',
            });
            if (!response.ok) throw new Error('Failed to delete tournament');
            return true;
        } catch (error) {
            console.error('Delete tournament error:', error);
            throw error;
        }
    },

    async getTournamentListWithDetails() {
        // Since the backend doesn't have an endpoint for this aggregated data yet, 
        // we fetch tournaments and then events for each, or we could just use the list 
        // if the backend `statistics` API provided this. For now, using the basic list.
        return this.getTournamentList();
    },

    // =========================================================================
    // Event APIs
    // =========================================================================

    async createEvent(eventData: any) {
        try {
            const payload: any = {
                tournament_id: eventData.tournament_id,
                event_name: eventData.event_name,
                event_type: eventData.event_type,
                is_team_event: eventData.is_team_event || false,
                status: 'REGISTRATION',
                start_time: eventData.start_time || null
            };

            if (eventData.rule_mode === 'preset' && eventData.rule_id) {
                payload.rule_id = eventData.rule_id;
            } else if (eventData.rule_mode === 'custom' && eventData.rules?.stages) {
                payload.custom_rule_config = {
                    preset: 'custom',
                    stages: eventData.rules.stages
                };
            }

            const response = await fetch(`${API_BASE_URL}/events/`, {
                method: 'POST',
                headers: getHeaders(),
                credentials: 'include',
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error("Create event error:", errorData);
                throw new Error('Failed to create event');
            }

            return await response.json();
        } catch (error) {
            console.error('Create event error:', error);
            throw error;
        }
    },

    async fetchRules(): Promise<any[]> {
        try {
            const response = await fetch(`${API_BASE_URL}/rules/`);
            if (!response.ok) throw new Error('Failed to fetch rules');
            const data = await response.json();
            return data.results || data;
        } catch (error) {
            console.error('Fetch rules error:', error);
            return [];
        }
    },

    async getEventsByTournamentId(tournamentId: string): Promise<any[]> {
        try {
            const response = await fetch(`${API_BASE_URL}/events/?tournament=${tournamentId}`);
            if (!response.ok) throw new Error('Failed to fetch events');
            const data = await response.json();
            return data.results || data;
        } catch (error) {
            console.error('Fetch events error:', error);
            return [];
        }
    },

    async getEventById(eventId: string) {
        try {
            const response = await fetch(`${API_BASE_URL}/events/${eventId}/`);
            if (!response.ok) throw new Error('Failed to fetch event');
            return await response.json();
        } catch (error) {
            console.error('Fetch event detail error:', error);
            return null;
        }
    },

    async updateEvent(eventId: string, eventData: any) {
        try {
            const response = await fetch(`${API_BASE_URL}/events/${eventId}/`, {
                method: 'PATCH',
                headers: getHeaders(),
                credentials: 'include',
                body: JSON.stringify(eventData),
            });
            if (!response.ok) throw new Error('Failed to update event');
            return await response.json();
        } catch (error) {
            console.error('Update event error:', error);
            throw error;
        }
    },

    async deleteEvent(eventId: string) {
        try {
            const response = await fetch(`${API_BASE_URL}/events/${eventId}/`, {
                method: 'DELETE',
                headers: getHeaders(),
                credentials: 'include',
            });
            if (!response.ok) throw new Error('Failed to delete event');
            return true;
        } catch (error) {
            console.error('Delete event error:', error);
            throw error;
        }
    },

    async saveCurrentStep(eventId: string, stepIndex: number) {
        return this.updateEvent(eventId, { current_step: stepIndex });
    },

    // =========================================================================
    // Fencer & Participants APIs
    // =========================================================================

    async saveFencers(fencerList: any[]) {
        try {
            const response = await fetch(`${API_BASE_URL}/fencers/bulk-save/`, {
                method: 'POST',
                headers: getHeaders(),
                credentials: 'include',
                body: JSON.stringify(fencerList),
            });

            if (!response.ok) {
                throw new Error('Failed to bulk save fencers');
            }

            const data = await response.json();
            return data.results || [];
        } catch (error) {
            console.error('Bulk save fencers error:', error);
            throw error;
        }
    },

    async syncEventFencers(eventId: string, currentFencerIds: string[]) {
        try {
            const response = await fetch(`${API_BASE_URL}/events/${eventId}/participants/sync/`, {
                method: 'PUT',
                headers: getHeaders(),
                credentials: 'include',
                body: JSON.stringify({ fencer_ids: currentFencerIds }),
            });

            if (!response.ok) {
                throw new Error('Failed to sync event fencers');
            }
            return true;
        } catch (error) {
            console.error('Sync fencers error:', error);
            throw error;
        }
    },

    async getFencersByEvent(eventId: string) {
        try {
            const response = await fetch(`${API_BASE_URL}/events/${eventId}/participants/`);
            if (!response.ok) throw new Error('Failed to fetch event participants');
            const data = await response.json();
            
            // Extract fencer objects from participants
            if (data.participants && Array.isArray(data.participants)) {
                return data.participants
                    .map((p: any) => p.fencer_info)
                    .filter((f: any) => f != null);
            }
            return [];
        } catch (error) {
            console.error('Fetch fencers by event error:', error);
            return [];
        }
    },

    async getFencerById(fencerId: string) {
        try {
            const response = await fetch(`${API_BASE_URL}/fencers/${fencerId}/`);
            if (!response.ok) throw new Error('Failed to fetch fencer');
            return await response.json();
        } catch (error) {
            console.error('Fetch fencer detail error:', error);
            return null;
        }
    },

    // =========================================================================
    // Live Ranking & Stage APIs
    // =========================================================================

    async initializeLiveRanking(eventId: string, initialFencers: any[]) {
        try {
            const sortedFencers = [...initialFencers].sort((a, b) => (a.current_ranking || 999) - (b.current_ranking || 999));
            
            const liveRanking = sortedFencers.map((fencer, index) => ({
                id: fencer.id,
                ranks: {0: index + 1},
                elimination_status: {0: false},
            }));

            const response = await fetch(`${API_BASE_URL}/events/${eventId}/live-ranking/`, {
                method: 'PUT',
                headers: getHeaders(),
                credentials: 'include',
                body: JSON.stringify({ live_ranking: liveRanking }),
            });

            if (!response.ok) throw new Error('Failed to initialize live ranking');
            return await response.json();
        } catch (error) {
            console.error('Initialize live ranking error:', error);
            throw error;
        }
    },

    async getLiveFencers(eventId: string) {
        try {
            const event = await this.getEventById(eventId);
            if (event && event.live_ranking && event.live_ranking.length > 0) {
                return event.live_ranking
                    .filter((f: any) => !f.is_eliminated)
                    .sort((a: any, b: any) => a.current_rank - b.current_rank);
            }
            return [];
        } catch (error) {
            console.error('Get live fencers error:', error);
            return [];
        }
    },

    async updateLiveRanking(eventId: string, rankingList: any[]) {
        try {
            const response = await fetch(`${API_BASE_URL}/events/${eventId}/live-ranking/`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ live_ranking: rankingList }),
            });

            if (!response.ok) throw new Error('Failed to update live ranking');
            return await response.json();
        } catch (error) {
            console.error('Update live ranking error:', error);
            throw error;
        }
    },

    async updateStageRanking(eventId: string, stageIndex: number, stageResults: {id: string, rank: number, is_eliminated: boolean}[]) {
        try {
            const event = await this.getEventById(eventId);
            if (!event || !event.live_ranking) return;

            const resultMap = new Map(stageResults.map(r => [r.id, r]));

            const newLiveRanking = event.live_ranking.map((fencer: any) => {
                const result = resultMap.get(fencer.id);
                const newRanks = {...fencer.ranks};
                const newEliminationStatus = {...fencer.elimination_status};

                Object.keys(newRanks).forEach(key => {
                    if (parseInt(key) >= stageIndex) delete newRanks[key];
                });
                Object.keys(newEliminationStatus).forEach(key => {
                    if (parseInt(key) >= stageIndex) delete newEliminationStatus[key];
                });

                if (result) {
                    newRanks[stageIndex] = result.rank;
                    newEliminationStatus[stageIndex] = result.is_eliminated;
                }

                return {
                    id: fencer.id,
                    ranks: newRanks,
                    elimination_status: newEliminationStatus,
                };
            });

            await this.updateLiveRanking(eventId, newLiveRanking);
        } catch (error) {
            console.error('Update stage ranking error:', error);
            throw error;
        }
    },

    async getFencersForStage(eventId: string, stageIndex: number) {
        try {
            const event = await this.getEventById(eventId);
            if (!event || !event.live_ranking) return [];

            const sourceStageIndex = stageIndex - 1;

            const relevantFencerStates = event.live_ranking
                .filter((f: any) => f.elimination_status[sourceStageIndex] === false);

            // Need to fetch details for these fencers
            // For MVP, we can fetch all event fencers and match them
            const allFencers = await this.getFencersByEvent(eventId);
            const fencerMap = new Map(allFencers.map((f: any) => [f.id, f]));

            const hydratedFencers = relevantFencerStates.map((state: any) => {
                const details = fencerMap.get(state.id) || { id: state.id };
                return {
                    ...details,
                    ranks: state.ranks,
                    elimination_status: state.elimination_status,
                    current_rank: state.ranks[sourceStageIndex],
                };
            });

            return hydratedFencers.sort((a: any, b: any) => a.current_rank - b.current_rank);
        } catch (error) {
            console.error('Get fencers for stage error:', error);
            return [];
        }
    },

    // =========================================================================
    // Pool APIs
    // =========================================================================

    async savePools(eventId: string, stageId: string, poolsData: any[][]) {
        try {
            // Convert to format expected by backend
            const formattedPools = poolsData.map((poolFencers, index) => ({
                pool_number: index + 1,
                fencer_ids: poolFencers.map(f => f.id)
            }));

            const response = await fetch(`${API_BASE_URL}/events/${eventId}/stages/${stageId}/pools/`, {
                method: 'POST',
                headers: getHeaders(),
                credentials: 'include',
                body: JSON.stringify(formattedPools),
            });

            if (!response.ok) throw new Error('Failed to save pools');
            return true;
        } catch (error) {
            console.error('Save pools error:', error);
            throw error;
        }
    },

    async getPoolsByStageId(eventId: string, stageId: string) {
        try {
            const response = await fetch(`${API_BASE_URL}/events/${eventId}/stages/${stageId}/pools/`);
            if (!response.ok) throw new Error('Failed to fetch pools');
            return await response.json();
        } catch (error) {
            console.error('Get pools error:', error);
            return [];
        }
    },

    // Legacy method for compatibility if still needed
    async getPoolsByEvent(eventId: string) {
        try {
            const response = await fetch(`${API_BASE_URL}/pools/by-event/${eventId}/`);
            if (!response.ok) throw new Error('Failed to fetch pools by event');
            return await response.json();
        } catch (error) {
            console.error('Get pools by event error:', error);
            return [];
        }
    },

    async getPoolsDetailed(eventId: string, stageId: string) {
        try {
            const poolDefinitions = await this.getPoolsByStageId(eventId, stageId);
            if (!poolDefinitions || poolDefinitions.length === 0) return null;

            // Sort by pool number
            poolDefinitions.sort((a: any, b: any) => a.pool_number - b.pool_number);

            // Fetch all fencers once to avoid N+1 queries
            const allFencers = await this.getFencersByEvent(eventId);
            const fencerMap = new Map(allFencers.map((f: any) => [f.id, f]));

            const detailedPools = poolDefinitions.map((pool: any) => {
                return (pool.fencer_ids || []).map((fId: string) => fencerMap.get(fId) || { id: fId });
            });

            return detailedPools;
        } catch (error) {
            console.error('Get detailed pools error:', error);
            return null;
        }
    },

    async updatePoolResults(poolId: string, results: any[][], stats: any[], isLocked: boolean) {
        try {
            const payload = {
                results,
                stats,
                is_locked: isLocked
            };

            const response = await fetch(`${API_BASE_URL}/pools/${poolId}/results/`, {
                method: 'PATCH',
                headers: getHeaders(),
                credentials: 'include',
                body: JSON.stringify(payload),
            });

            if (!response.ok) throw new Error('Failed to update pool results');
            return true;
        } catch (error) {
            console.error('Update pool results error:', error);
            return false;
        }
    },

    async getEventPoolRanking(eventId: string, stageId: string) {
        try {
            const pools = await this.getPoolsByStageId(eventId, stageId);
            if (!pools || pools.length === 0) return [];

            const rankingData = [];
            const allFencers = await this.getFencersByEvent(eventId);
            const fencerMap = new Map(allFencers.map((f: any) => [f.id, f]));

            for (const pool of pools) {
                if (!pool.stats || !pool.fencer_ids) continue;

                const matchCount = pool.fencer_ids.length - 1;

                for (let i = 0; i < pool.fencer_ids.length; i++) {
                    const fencerId = pool.fencer_ids[i];
                    const fStats = pool.stats[i];
                    const fencer = fencerMap.get(fencerId);

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
            console.error('Get pool ranking error:', error);
            return [];
        }
    },

    // =========================================================================
    // DE Tree APIs
    // =========================================================================

    async getQualifiedFencersForDE(eventId: string, stageId: string) {
        try {
            const allRanked = await this.getEventPoolRanking(eventId, stageId);

            const sorted = allRanked.sort((a, b) => {
                if (b.v_m !== a.v_m) return b.v_m - a.v_m;
                if (b.ind !== a.ind) return b.ind - a.ind;
                return b.ts - a.ts;
            });

            // 假设取前 80%
            const cutoff = Math.ceil(sorted.length * 0.8);
            return sorted.slice(0, cutoff).map((f, index) => ({
                ...f,
                seed: index + 1
            }));
        } catch (error) {
            console.error('Get qualified fencers error:', error);
            return [];
        }
    },

    async saveDETree(eventId: string, stageId: string, bracketData: any[][]) {
        try {
            const response = await fetch(`${API_BASE_URL}/events/${eventId}/stages/${stageId}/detree/`, {
                method: 'PUT',
                headers: getHeaders(),
                credentials: 'include',
                body: JSON.stringify({ tree_data: bracketData }),
            });

            if (!response.ok) throw new Error('Failed to save DE tree');
            return true;
        } catch (error) {
            console.error('Save DE tree error:', error);
            throw error;
        }
    },

    async getDETree(eventId: string, stageId: string) {
        try {
            const response = await fetch(`${API_BASE_URL}/events/${eventId}/stages/${stageId}/detree/`);
            if (!response.ok) throw new Error('Failed to fetch DE tree');
            return await response.json();
        } catch (error) {
            console.error('Get DE tree error:', error);
            return null;
        }
    },

    async getFinalRanking(eventId: string, stageId: string) {
        try {
            const poolRanking = await this.getEventPoolRanking(eventId, stageId);
            if (!poolRanking || poolRanking.length === 0) return [];

            const baseRankedFencers = poolRanking.sort((a, b) => {
                if (b.v_m !== a.v_m) return b.v_m - a.v_m;
                if (b.ind !== a.ind) return b.ind - a.ind;
                return b.ts - a.ts;
            }).map((f, index) => ({
                ...f,
                pool_rank: index + 1
            }));

            const deTree = await this.getDETree(eventId, stageId);
            if (!deTree || deTree.length === 0) {
                return baseRankedFencers.map(f => ({...f, last_round: '小组赛'}));
            }

            const eliminationMap = new Map<string, string>();
            const totalRounds = deTree.length;

            const finalMatch = totalRounds > 0 ? deTree[totalRounds - 1][0] : null;
            const semiFinals = totalRounds > 1 ? deTree[totalRounds - 2] : [];

            if (finalMatch && finalMatch.winnerId) {
                const winnerId = String(finalMatch.winnerId);
                const runnerUp = finalMatch.fencerA?.id === finalMatch.winnerId ? finalMatch.fencerB : finalMatch.fencerA;
                if (runnerUp) {
                    eliminationMap.set(winnerId, "冠军 (Gold)");
                    eliminationMap.set(String(runnerUp.id), "亚军 (Silver)");
                }
            }

            semiFinals.forEach((match: any) => {
                if (match.winnerId) {
                    const loser = match.fencerA?.id === match.winnerId ? match.fencerB : match.fencerA;
                    if (loser && !eliminationMap.has(String(loser.id))) {
                        eliminationMap.set(String(loser.id), "季军 (Bronze)");
                    }
                }
            });

            deTree.forEach((round: any[], rIdx: number) => {
                const roundName = `Table of ${Math.pow(2, totalRounds - rIdx)}`;
                round.forEach((match: any) => {
                    const loser = match.winnerId
                        ? (String(match.winnerId) === String(match.fencerA?.id) ? match.fencerB : match.fencerA)
                        : null;

                    if (loser && !eliminationMap.has(String(loser.id))) {
                        eliminationMap.set(String(loser.id), roundName);
                    }
                });
            });

            const fullResults = baseRankedFencers.map(fencer => ({
                ...fencer,
                last_round: eliminationMap.get(String(fencer.id)) || '小组赛'
            }));

            const roundOrder = [
                "冠军 (Gold)",
                "亚军 (Silver)",
                "季军 (Bronze)",
                "Table of 4",
                "Table of 8",
                "Table of 16",
                "Table of 32",
                "Table of 64",
                "小组赛",
            ];

            fullResults.sort((a, b) => {
                const rankA = roundOrder.indexOf(a.last_round);
                const rankB = roundOrder.indexOf(b.last_round);

                if (rankA !== rankB) {
                    return rankA - rankB;
                }
                return a.pool_rank - b.pool_rank;
            });

            return fullResults;
        } catch (error) {
            console.error('Get final ranking error:', error);
            return [];
        }
    }
};