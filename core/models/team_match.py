from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class TeamMatch:
    """6.1. Team_Match（团体淘汰赛）"""
    event_id: UUID = field(metadata={"foreign_key": "Event", "description": "所属项目"})
    phase_id: UUID = field(metadata={"foreign_key": "Event_Phase", "description": "比赛阶段"})
    match_code: str = field(metadata={"max_length": 20, "description": "比赛编号 (NOT NULL)"})
    status_id: UUID = field(metadata={"foreign_key": "Match_Status_Type", "description": "比赛状态"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    team_a_id: Optional[UUID] = field(default=None, metadata={"foreign_key": "Team", "description": "队伍A"})
    team_b_id: Optional[UUID] = field(default=None, metadata={"foreign_key": "Team", "description": "队伍B"})
    winner_team_id: Optional[UUID] = field(default=None, metadata={"foreign_key": "Team", "description": "获胜队伍"})
    team_a_score: int = field(default=0, metadata={"description": "队伍A总分"})
    team_b_score: int = field(default=0, metadata={"description": "队伍B总分"})
    match_number: Optional[int] = field(default=None, metadata={"description": "比赛序号"})
    piste_id: Optional[UUID] = field(default=None, metadata={"foreign_key": "Piste", "description": "比赛剑道"})
    scheduled_time: Optional[datetime] = field(default=None, metadata={"description": "计划时间"})
    actual_start_time: Optional[datetime] = field(default=None, metadata={"description": "实际开始"})
    actual_end_time: Optional[datetime] = field(default=None, metadata={"description": "实际结束"})
    duration_minutes: Optional[int] = field(default=None, metadata={"description": "持续时间（分钟）"})
    forfeit_type_id: Optional[UUID] = field(default=None,
                                            metadata={"foreign_key": "Forfeit_Type", "description": "退赛类型"})
    forfeit_notes: Optional[str] = field(default=None, metadata={"description": "退赛说明"})
    created_at: datetime = field(default_factory=datetime.now,
                                 metadata={"description": "创建时间", "db_default": "NOW()"})
    updated_at: datetime = field(default_factory=datetime.now,
                                 metadata={"description": "更新时间", "db_default": "NOW()"})
