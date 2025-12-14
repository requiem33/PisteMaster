from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class PoolBout:
    """4.3. PoolBout（小组赛单场）"""
    pool_id: UUID = field(metadata={"foreign_key": "Pool", "description": "所属小组"})
    fencer_a_id: UUID = field(metadata={"foreign_key": "Fencer", "description": "运动员A"})
    fencer_b_id: UUID = field(metadata={"foreign_key": "Fencer", "description": "运动员B"})
    status_id: UUID = field(metadata={"foreign_key": "Match_Status_Type", "description": "比赛状态"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    winner_id: Optional[UUID] = field(default=None, metadata={"foreign_key": "Fencer", "description": "获胜者"})
    fencer_a_score: int = field(default=0, metadata={"description": "A得分"})
    fencer_b_score: int = field(default=0, metadata={"description": "B得分"})
    scheduled_time: Optional[datetime] = field(default=None, metadata={"description": "计划时间"})
    actual_start_time: Optional[datetime] = field(default=None, metadata={"description": "实际开始时间"})
    actual_end_time: Optional[datetime] = field(default=None, metadata={"description": "实际结束时间"})
    duration_seconds: Optional[int] = field(default=None, metadata={"description": "持续时间（秒）"})
    notes: Optional[str] = field(default=None, metadata={"description": "备注"})

    # 约束: CHECK(fencer_a_id != fencer_b_id)
    # 约束: UNIQUE(pool_id, LEAST(fencer_a_id, fencer_b_id), GREATEST(fencer_a_id, fencer_b_id))
