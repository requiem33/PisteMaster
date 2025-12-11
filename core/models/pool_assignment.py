from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass
class PoolAssignment:
    """4.2. Pool_Assignment（小组赛排名）"""
    pool_id: UUID = field(metadata={"foreign_key": "Pool", "description": "所属小组"})
    fencer_id: UUID = field(metadata={"foreign_key": "Fencer", "description": "运动员"})
    final_pool_rank: int = field(metadata={"description": "最终排名 (NOT NULL)", "constraint": "CHECK(> 0)"})

    victories: int = field(default=0, metadata={"description": "胜场数(V)"})
    indicator: int = field(default=0, metadata={"description": "得失分差(Ind) - 计算得出"})
    touches_scored: int = field(default=0, metadata={"description": "总得分(TS)"})
    touches_received: int = field(default=0, metadata={"description": "总失分(TR)"})
    matches_played: int = field(default=0, metadata={"description": "已赛场次"})
    is_qualified: bool = field(default=False, metadata={"description": "是否晋级"})
    qualification_rank: Optional[int] = field(default=None, metadata={"description": "晋级排名"})

    # 组合主键 (pool_id, fencer_id) 和 UNIQUE(pool_id, final_pool_rank) 需在 ORM 层面处理
