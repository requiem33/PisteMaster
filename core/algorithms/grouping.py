# core/algorithms/grouping.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import random


@dataclass
class GroupingConfig:
    """分组配置"""
    pool_size: int = 7  # 每组人数
    min_pool_size: int = 3  # 最小人数（否则合并）
    seed_protection: bool = True  # 种子保护
    avoid_same_club: bool = True  # 回避同俱乐部选手


class GroupingAlgorithm:
    """分组算法基类"""

    @staticmethod
    def snake_seeding(participants: List[int], pool_count: int) -> List[List[int]]:
        """
        蛇形编排法（标准击剑分组算法）。

        参数:
            participants: 选手ID列表，应按种子顺序排列（种子1在前）
            pool_count: 要分成几组

        返回:
            分组列表，每个内层列表是一组选手ID
        """
        groups = [[] for _ in range(pool_count)]

        for i, participant_id in enumerate(participants):
            # 决定放在哪一组
            group_index = i % pool_count

            # 蛇形：偶数行正向，奇数行反向
            if (i // pool_count) % 2 == 1:
                group_index = pool_count - 1 - group_index

            groups[group_index].append(participant_id)

        return groups

    @staticmethod
    def create_pools(
            participants: List[int],
            config: GroupingConfig
    ) -> Dict[str, Any]:
        """
        创建小组赛分组（完整流程）。

        返回结构:
        {
            "pools": [[选手ID列表], ...],
            "pool_count": 组数,
            "participants_per_pool": [每组成员数, ...],
            "seed_placement": {种子位置: 组索引, ...}
        }
        """
        # 1. 计算组数
        total_participants = len(participants)
        pool_count = (total_participants + config.pool_size - 1) // config.pool_size

        # 2. 调整组数以满足最小人数要求
        while (total_participants / pool_count) < config.min_pool_size and pool_count > 1:
            pool_count -= 1

        # 3. 蛇形编排
        pools = GroupingAlgorithm.snake_seeding(participants, pool_count)

        # 4. 记录种子位置（用于验证）
        seed_placement = {}
        for seed_rank, participant_id in enumerate(participants[:pool_count]):
            # 前N号种子应该在不同组
            for pool_idx, pool in enumerate(pools):
                if participant_id in pool:
                    seed_placement[seed_rank + 1] = pool_idx
                    break

        return {
            "pools": pools,
            "pool_count": pool_count,
            "participants_per_pool": [len(pool) for pool in pools],
            "seed_placement": seed_placement
        }