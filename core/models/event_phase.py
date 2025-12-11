from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class EventPhase:
    """5.1. Event_Phase（项目阶段）"""
    event_id: UUID = field(metadata={"foreign_key": "Event", "description": "所属项目"})
    phase_code: str = field(metadata={"max_length": 30, "description": "阶段代码 (NOT NULL)"})
    display_name: str = field(metadata={"max_length": 50, "description": "显示名称 (NOT NULL)"})
    phase_order: int = field(metadata={"description": "阶段顺序 (NOT NULL)"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    is_elimination: bool = field(default=True, metadata={"description": "是否为淘汰赛"})
    target_score: Optional[int] = field(default=None, metadata={"description": "目标分数"})
    is_final_phase: bool = field(default=False, metadata={"description": "是否为决赛阶段"})
