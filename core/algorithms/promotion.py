# core/algorithms/promotion.py
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from ..models.match import PoolMatch, MatchStatus


@dataclass
class PoolRanking:
    """小组赛排名结果"""
    fencer_id: int
    victories: int  # 胜场数
    hits_scored: int  # 击中剑数
    hits_received: int  # 被击中剑数
    indicator: int  # 净胜剑数 (hits_scored - hits_received)
    rank: int  # 小组内排名

    @property
    def matches_played(self) -> int:
        """计算比赛场数（根据击剑规则可能需要）"""
        return self.victories + self.losses  # 需要记录负场


class PromotionAlgorithm:
    """晋级算法（击剑TIE-BREAK规则）"""

    @staticmethod
    def calculate_pool_ranking(pool_matches: List[PoolMatch]) -> List[PoolRanking]:
        """
        计算小组赛排名（根据国际剑联TIE-BREAK规则）。

        排名规则（按优先级）:
        1. 胜场数 (Victories)
        2. 净胜剑数 (Indicator)
        3. 击中剑数 (Hits Scored)
        4. 直接对决结果 (如果仅两人平局)
        5. 抽签

        返回:
            按排名排序的 PoolRanking 列表
        """
        # 初始化选手数据
        fencer_stats: Dict[int, Dict[str, int]] = {}

        # 统计比赛结果
        for match in pool_matches:
            if match.status != MatchStatus.COMPLETED:
                continue

            # 初始化选手记录
            for fencer_id in [match.fencer_a_id, match.fencer_b_id]:
                if fencer_id not in fencer_stats:
                    fencer_stats[fencer_id] = {
                        'victories': 0,
                        'hits_scored': 0,
                        'hits_received': 0,
                        'matches_against': {}  # 记录对每位对手的结果
                    }

            # 记录击中数
            fencer_stats[match.fencer_a_id]['hits_scored'] += match.score_a
            fencer_stats[match.fencer_a_id]['hits_received'] += match.score_b

            fencer_stats[match.fencer_b_id]['hits_scored'] += match.score_b
            fencer_stats[match.fencer_b_id]['hits_received'] += match.score_a

            # 记录胜负
            if match.score_a > match.score_b:
                fencer_stats[match.fencer_a_id]['victories'] += 1
                fencer_stats[match.fencer_a_id]['matches_against'][match.fencer_b_id] = 'win'
                fencer_stats[match.fencer_b_id]['matches_against'][match.fencer_a_id] = 'loss'
            elif match.score_b > match.score_a:
                fencer_stats[match.fencer_b_id]['victories'] += 1
                fencer_stats[match.fencer_b_id]['matches_against'][match.fencer_a_id] = 'win'
                fencer_stats[match.fencer_a_id]['matches_against'][match.fencer_b_id] = 'loss'
            else:
                # 平局（某些规则允许）
                fencer_stats[match.fencer_a_id]['matches_against'][match.fencer_b_id] = 'draw'
                fencer_stats[match.fencer_b_id]['matches_against'][match.fencer_a_id] = 'draw'

        # 转换为排名对象
        rankings = []
        for fencer_id, stats in fencer_stats.items():
            indicator = stats['hits_scored'] - stats['hits_received']
            rankings.append(PoolRanking(
                fencer_id=fencer_id,
                victories=stats['victories'],
                hits_scored=stats['hits_scored'],
                hits_received=stats['hits_received'],
                indicator=indicator,
                rank=0  # 稍后确定
            ))

        # 按TIE-BREAK规则排序
        rankings.sort(key=lambda x: (
            -x.victories,  # 胜场数降序
            -x.indicator,  # 净胜剑数降序
            -x.hits_scored,  # 击中剑数降序
            x.fencer_id  # 最后按ID稳定排序
        ))

        # 处理平局（直接对决）
        for i in range(len(rankings) - 1):
            if (rankings[i].victories == rankings[i + 1].victories and
                    rankings[i].indicator == rankings[i + 1].indicator and
                    rankings[i].hits_scored == rankings[i + 1].hits_scored):

                # 检查直接对决结果
                fencer_a = rankings[i].fencer_id
                fencer_b = rankings[i + 1].fencer_id

                if (fencer_b in fencer_stats[fencer_a]['matches_against'] and
                        fencer_stats[fencer_a]['matches_against'][fencer_b] == 'win'):
                    # fencer_a直接战胜了fencer_b，保持顺序
                    pass
                elif (fencer_a in fencer_stats[fencer_b]['matches_against'] and
                      fencer_stats[fencer_b]['matches_against'][fencer_a] == 'win'):
                    # fencer_b直接战胜了fencer_a，交换位置
                    rankings[i], rankings[i + 1] = rankings[i + 1], rankings[i]

        # 分配最终排名
        for i, ranking in enumerate(rankings):
            ranking.rank = i + 1

        return rankings

    @staticmethod
    def promote_from_pools(
            all_pools_rankings: List[List[PoolRanking]],
            promotion_count: int = 4
    ) -> List[int]:
        """
        从所有小组中选拔晋级选手。

        参数:
            all_pools_rankings: 每个小组的排名列表
            promotion_count: 每组晋级人数

        返回:
            晋级选手ID列表（按淘汰赛种子顺序）
        """
        promoted_fencers = []

        # 收集每组前N名
        for pool_rankings in all_pools_rankings:
            for i in range(min(promotion_count, len(pool_rankings))):
                promoted_fencers.append(pool_rankings[i].fencer_id)

        # 按种子顺序排序（通常：小组第1优先于小组第2等）
        # 在实际击剑比赛中，可能需要更复杂的重新排序逻辑
        return promoted_fencers