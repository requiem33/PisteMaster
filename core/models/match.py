from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional


@dataclass
class Match:
    """5.2. Match（个人淘汰赛）"""

    event_id: UUID = field(metadata={"foreign_key": "Event", "description": "所属项目"})
    phase_id: UUID = field(
        metadata={"foreign_key": "Event_Phase", "description": "比赛阶段"}
    )
    match_code: str = field(
        metadata={"max_length": 20, "description": "比赛编号 (NOT NULL, UNIQUE)"}
    )
    status_id: UUID = field(
        metadata={"foreign_key": "Match_Status_Type", "description": "比赛状态"}
    )

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    fencer_a_id: Optional[UUID] = field(
        default=None, metadata={"foreign_key": "Fencer", "description": "运动员A"}
    )
    fencer_b_id: Optional[UUID] = field(
        default=None, metadata={"foreign_key": "Fencer", "description": "运动员B"}
    )
    winner_id: Optional[UUID] = field(
        default=None, metadata={"foreign_key": "Fencer", "description": "获胜者"}
    )
    fencer_a_score: int = field(default=0, metadata={"description": "A得分"})
    fencer_b_score: int = field(default=0, metadata={"description": "B得分"})
    match_number: Optional[int] = field(
        default=None, metadata={"description": "比赛序号"}
    )
    piste_id: Optional[UUID] = field(
        default=None, metadata={"foreign_key": "Piste", "description": "比赛剑道"}
    )
    scheduled_time: Optional[datetime] = field(
        default=None, metadata={"description": "计划时间"}
    )
    actual_start_time: Optional[datetime] = field(
        default=None, metadata={"description": "实际开始"}
    )
    actual_end_time: Optional[datetime] = field(
        default=None, metadata={"description": "实际结束"}
    )
    duration_minutes: Optional[int] = field(
        default=None, metadata={"description": "持续时间（分钟）"}
    )
    forfeit_type_id: Optional[UUID] = field(
        default=None,
        metadata={"foreign_key": "Forfeit_Type", "description": "退赛类型"},
    )
    forfeit_notes: Optional[str] = field(
        default=None, metadata={"description": "退赛说明"}
    )
    created_at: datetime = field(
        default_factory=datetime.now,
        metadata={"description": "创建时间", "db_default": "NOW()"},
    )
    updated_at: datetime = field(
        default_factory=datetime.now,
        metadata={"description": "更新时间", "db_default": "NOW()"},
    )
