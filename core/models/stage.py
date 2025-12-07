# core/models/stage.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from core.models.match import PoolMatch


class StageType(Enum):
    """比赛阶段类型"""
    POOL = 'pool'  # 小组赛
    DIRECT_ELIMINATION = 'direct_elimination'  # 淘汰赛
    ROUND_ROBIN = 'round_robin'  # 循环赛（可选扩展）


class StageStatus(Enum):
    """阶段状态"""
    SCHEDULED = 'scheduled'  # 已编排
    ONGOING = 'ongoing'  # 进行中
    COMPLETED = 'completed'  # 已结束
    CANCELLED = 'cancelled'  # 已取消


@dataclass
class CompetitionStage:
    """
    比赛阶段基类。
    一个比赛单项（CompetitionItem）可以包含多个阶段（如：小组赛→淘汰赛）。
    """
    name: str  # 如“小组赛A组”、“64强赛”
    stage_type: StageType
    competition_item_id: int  # 所属比赛单项ID

    # 编排配置
    participant_ids: List[int] = field(default_factory=list)  # 本阶段参赛选手ID
    rules_override: Optional[Dict[str, Any]] = None  # 阶段特定规则（可覆盖单项规则）

    # 状态与进度
    status: StageStatus = StageStatus.SCHEDULED
    current_round: int = 0  # 当前轮次（淘汰赛有意义）
    total_rounds: int = 1  # 总轮次

    # 关联
    id: Optional[int] = field(default=None, compare=False)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def is_individual(self) -> bool:
        """是否为个人赛阶段（继承自比赛单项，未来可扩展团体赛）"""
        # 注：实际项目中可能需要从CompetitionItem获取
        return True

    def add_participant(self, fencer_id: int) -> bool:
        """添加选手到本阶段"""
        if fencer_id not in self.participant_ids:
            self.participant_ids.append(fencer_id)
            return True
        return False

    def can_start(self) -> tuple[bool, str]:
        """检查是否可以开始本阶段"""
        if self.status != StageStatus.SCHEDULED:
            return False, f"阶段状态为 {self.status.value}，无法开始"
        if len(self.participant_ids) < 2:
            return False, "至少需要2名选手"
        return True, ""


@dataclass
class PoolStage(CompetitionStage):
    """小组赛阶段（具体化）"""
    pool_size: int = 7  # 每组人数
    pools: List[List[int]] = field(default_factory=list)  # 分组列表，每个子列表是一组选手ID

    def generate_pools(self, seed_order: List[int] = None) -> List[List[int]]:
        """
        根据蛇形编排法生成小组分组。
        seed_order: 种子顺序列表（从高到低），如果为None则使用participant_ids
        """
        participants = seed_order or self.participant_ids
        if not participants:
            return []

        pool_count = (len(participants) + self.pool_size - 1) // self.pool_size
        self.pools = [[] for _ in range(pool_count)]

        # 蛇形编排：1,2,3,4,5,6,7,8 -> 分组: [1,6,7], [2,5,8], [3,4]
        for i, fencer_id in enumerate(participants):
            pool_idx = i % pool_count
            if (i // pool_count) % 2 == 1:  # 反向填充
                pool_idx = pool_count - 1 - pool_idx
            self.pools[pool_idx].append(fencer_id)

        return self.pools

    def generate_pool_matches(self) -> List[PoolMatch]:
        """为所有小组生成循环赛对阵表"""
        matches = []
        for pool_idx, pool_fencers in enumerate(self.pools):
            # 生成小组内所有组合（循环赛）
            for i in range(len(pool_fencers)):
                for j in range(i + 1, len(pool_fencers)):
                    match = PoolMatch(
                        fencer_a_id=pool_fencers[i],
                        fencer_b_id=pool_fencers[j],
                        stage_id=self.id,
                        pool_round=1  # 可扩展为多轮
                    )
                    matches.append(match)
        return matches
