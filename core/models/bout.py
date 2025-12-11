from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Bout:
    """6.3. Bout（团体赛单局接力）"""
    team_match_id: UUID = field(metadata={"foreign_key": "Team_Match", "description": "所属团体赛"})
    bout_number: int = field(metadata={"description": "局次（1-9）(NOT NULL)"})
    status_id: UUID = field(metadata={"foreign_key": "Match_Status_Type", "description": "本局状态"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    fencer_a_id: Optional[UUID] = field(default=None, metadata={"foreign_key": "Fencer", "description": "A队上场选手"})
    fencer_b_id: Optional[UUID] = field(default=None, metadata={"foreign_key": "Fencer", "description": "B队上场选手"})
    fencer_a_score: int = field(default=0, metadata={"description": "选手A结束时比分"})
    fencer_b_score: int = field(default=0, metadata={"description": "选手B结束时比分"})
    start_score_a: int = field(default=0, metadata={"description": "A队起始比分"})
    start_score_b: int = field(default=0, metadata={"description": "B队起始比分"})
    target_score: Optional[int] = field(default=None, metadata={"description": "本局目标分数"})
    start_time: Optional[datetime] = field(default=None, metadata={"description": "开始时间"})
    end_time: Optional[datetime] = field(default=None, metadata={"description": "结束时间"})
    duration_seconds: Optional[int] = field(default=None, metadata={"description": "持续时间（秒）"})
