export interface Tournament {
    id: string;               // UUID 或 临时ID
    tournament_name: string;
    organizer: string;
    location: string;
    start_date: string;
    end_date: string;
    status: 'draft' | 'active' | 'completed';
    is_synced: boolean;       // 离线同步标识
    updated_at: number;
}