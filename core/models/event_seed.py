from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from _decimal import Decimal


@dataclass
class EventSeed:
    """3.5. Event_Seed（项目种子排名）"""
    event_id: UUID = field(metadata={"foreign_key": "Event", "description": "所属项目"})
    fencer_id: UUID = field(metadata={"foreign_key": "Fencer", "description": "运动员"})
    seed_type_id: UUID = field(metadata={"foreign_key": "Seed_Type", "description": "种子类型"})
    seed_rank: int = field(metadata={"description": "种子排名 (NOT NULL)"})

    seed_value: Optional[Decimal] = field(default=None,
                                          metadata={"decimal_precision": (10, 2), "description": "种子分值"})

    # 组合主键 (event_id, fencer_id) 必须在 ORM 层面处理
