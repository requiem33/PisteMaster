from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime


@dataclass
class EventParticipant:
    """Event-Fencer关联（项目参与者）"""
    event_id: UUID = field(metadata={"foreign_key": "Event", "description": "所属项目"})
    fencer_id: UUID = field(metadata={"foreign_key": "Fencer", "description": "运动员"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    seed_rank: Optional[int] = field(default=None, metadata={"description": "种子排名"})
    seed_value: Optional[float] = field(default=None, metadata={"description": "种子分值"})
    is_confirmed: bool = field(default=True, metadata={"description": "是否确认参赛"})
    registration_time: Optional[datetime] = field(default=None, metadata={"description": "报名时间"})
    notes: Optional[str] = field(default=None, metadata={"description": "备注"})
    created_at: datetime = field(default_factory=datetime.now, metadata={"description": "创建时间"})
    updated_at: datetime = field(default_factory=datetime.now, metadata={"description": "更新时间"})
