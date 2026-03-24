from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


@dataclass
class Pool:
    """4.1. Pool（小组）"""

    event_id: UUID = field(metadata={"foreign_key": "Event", "description": "所属项目"})
    pool_number: int = field(metadata={"description": "小组编号 (NOT NULL)"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    piste_id: Optional[UUID] = field(
        default=None, metadata={"foreign_key": "Piste", "description": "分配剑道"}
    )
    start_time: Optional[datetime] = field(
        default=None, metadata={"description": "计划开始时间"}
    )
    fencer_ids: List[str] = field(
        default_factory=list, metadata={"description": "组内运动员ID列表"}
    )
    results: List[Dict[str, Any]] = field(
        default_factory=list, metadata={"description": "比赛结果矩阵"}
    )
    stats: List[Dict[str, Any]] = field(
        default_factory=list, metadata={"description": "比赛统计"}
    )
    status: str = field(
        default="SCHEDULED", metadata={"max_length": 20, "description": "状态"}
    )
    is_completed: bool = field(default=False, metadata={"description": "是否完成"})

    # UNIQUE(event_id, pool_number) 约束需在 ORM 层面处理
