from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
from ..models.match import PoolMatch, DirectEliminationMatch
from ..models.stage import CompetitionStage
from ..models.enums import StageType, MatchStatus


class MatchGenerationAlgorithm:
    """对阵生成算法"""

    @staticmethod
    def generate_pool_matches(
            pool: List[int],
            stage_id: int,
            pool_round: int = 1,
            start_time: Optional[datetime] = None
    ) -> List[PoolMatch]:
        """
        为单个小组生成循环赛对阵表。

        参数:
            pool: 小组内选手ID列表
            stage_id: 所属阶段ID
            pool_round: 小组赛轮次
            start_time: 第一场比赛开始时间

        返回:
            PoolMatch 对象列表
        """
        matches = []

        # 生成所有可能的组合（循环赛）
        for i in range(len(pool)):
            for j in range(i + 1, len(pool)):
                match_time = None
                if start_time:
                    # 简单的时间安排：每场比赛间隔10分钟
                    match_index = len(matches)
                    match_time = start_time + timedelta(minutes=match_index * 10)

                match = PoolMatch(
                    fencer_a_id=pool[i],
                    fencer_b_id=pool[j],
                    stage_id=stage_id,
                    pool_round=pool_round,
                    scheduled_time=match_time,
                    status=MatchStatus.SCHEDULED
                )
                matches.append(match)

        return matches

    @staticmethod
    def generate_all_pool_matches(
            pools: List[List[int]],
            stage_id: int,
            start_time: datetime
    ) -> List[PoolMatch]:
        """为所有小组生成对阵表"""
        all_matches = []

        for pool_idx, pool in enumerate(pools):
            # 可以为不同小组安排在不同时间或剑道
            pool_start_time = start_time + timedelta(hours=pool_idx * 2)
            pool_matches = MatchGenerationAlgorithm.generate_pool_matches(
                pool, stage_id, start_time=pool_start_time
            )
            all_matches.extend(pool_matches)

        return all_matches

    @staticmethod
    def generate_elimination_bracket(
            participants: List[int],
            stage_id: int,
            bracket_type: str = "single_elimination"
    ) -> List[DirectEliminationMatch]:
        """
        生成淘汰赛对阵表（单败淘汰）。

        参数:
            participants: 参赛选手ID列表（通常按种子顺序）
            stage_id: 所属阶段ID
            bracket_type: 淘汰赛类型

        返回:
            DirectEliminationMatch 对象列表
        """
        # 确保选手数是2的幂次，否则添加轮空
        n = len(participants)
        next_power_of_two = 1
        while next_power_of_two < n:
            next_power_of_two <<= 1

        # 为轮空选手添加占位符（-1表示轮空）
        bracket_participants = participants + [-1] * (next_power_of_two - n)

        matches = []
        round_number = 1
        total_rounds = next_power_of_two.bit_length() - 1

        # 第一轮：64强、32强等
        current_round_matches = []
        for i in range(0, len(bracket_participants), 2):
            pos = i // 2 + 1
            bracket_position = f"round{round_number}_match{pos}"

            match = DirectEliminationMatch(
                fencer_a_id=bracket_participants[i],
                fencer_b_id=bracket_participants[i + 1],
                stage_id=stage_id,
                bracket_position=bracket_position,
                round_number=round_number,
                status=MatchStatus.SCHEDULED
            )
            current_round_matches.append(match)
            matches.append(match)

        # 后续轮次
        match_id_counter = 0
        while len(current_round_matches) > 1:
            round_number += 1
            next_round_matches = []

            for i in range(0, len(current_round_matches), 2):
                pos = i // 2 + 1
                bracket_position = f"round{round_number}_match{pos}"

                match = DirectEliminationMatch(
                    fencer_a_id=-1,  # 将由胜者填入
                    fencer_b_id=-1,
                    stage_id=stage_id,
                    bracket_position=bracket_position,
                    round_number=round_number,
                    status=MatchStatus.SCHEDULED
                )

                # 设置前一回合的 next_match_id
                if i < len(current_round_matches):
                    current_round_matches[i].next_match_id = match_id_counter
                if i + 1 < len(current_round_matches):
                    current_round_matches[i + 1].next_match_id = match_id_counter

                matches.append(match)
                next_round_matches.append(match)
                match_id_counter += 1

            current_round_matches = next_round_matches

        return matches