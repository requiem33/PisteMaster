from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Optional


@dataclass
class PoolAssignment:
    """4.2. Pool_Assignment（小组赛排名）"""
    pool_id: UUID = field(metadata={"foreign_key": "Pool", "description": "所属小组"})
    fencer_id: UUID = field(metadata={"foreign_key": "Fencer", "description": "运动员"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    final_pool_rank: Optional[int] = field(default=None, metadata={"description": "最终排名"})
    victories: int = field(default=0, metadata={"description": "胜场数(V)"})
    indicator: int = field(default=0, metadata={"description": "得失分差(Ind)"})
    touches_scored: int = field(default=0, metadata={"description": "总得分(TS)"})
    touches_received: int = field(default=0, metadata={"description": "总失分(TR)"})
    matches_played: int = field(default=0, metadata={"description": "已赛场次"})
    is_qualified: bool = field(default=False, metadata={"description": "是否晋级"})
    qualification_rank: Optional[int] = field(default=None, metadata={"description": "晋级排名"})

    # 约束: UNIQUE(pool_id, final_pool_rank)
    # 约束: CHECK(final_pool_rank > 0)
