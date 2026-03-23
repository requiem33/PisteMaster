export interface Tournament {
    id: string;
    tournament_name: string;
    organizer: string;
    location: string;
    start_date: string;
    end_date: string;
    status: 'draft' | 'active' | 'completed';
    is_synced: boolean;
    updated_at: number;
}

export interface Stage {
    id: string;
    name: string;
    type: 'pool' | 'de';
    config?: {
        byes?: number;
        hits?: number;
        elimination_rate?: number;
        final_stage?: string;
        rank_to?: number;
    };
}