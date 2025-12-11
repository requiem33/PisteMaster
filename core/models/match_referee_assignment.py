from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class MatchRefereeAssignment:
    """7.2. Match_Referee_Assignment（比赛裁判分配）"""
    match_id: UUID = field(metadata={"description": "比赛ID (NOT NULL)"})
    match_type: str = field(metadata={"max_length": 10, "description": "比赛类型: INDIVIDUAL/TEAM (NOT NULL)"})
    referee_id: UUID = field(metadata={"foreign_key": "Referee", "description": "裁判"})
    role_id: UUID = field(metadata={"foreign_key": "Referee_Role", "description": "角色"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    assignment_order: int = field(default=1, metadata={"description": "分配顺序"})
    assigned_at: datetime = field(default_factory=datetime.now,
                                  metadata={"description": "分配时间", "db_default": "NOW()"})
