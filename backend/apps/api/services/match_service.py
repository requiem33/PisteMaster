# backend/apps/api/services/match_service.py
"""
比赛生成服务
"""
from typing import List, Optional
from django.db import transaction
from datetime import datetime, timedelta

from core.algorithms.matching import MatchGenerationAlgorithm
from ..models import CompetitionItem, Match, Fencer


class MatchGenerationService:
    """比赛生成服务"""

    @staticmethod
    def generate_pool_matches(
        competition_item_id: int,
        pool_size: int = 7,
        start_time: Optional[datetime] = None
    ) -> List[Match]:
        """
        生成小组赛

        参数:
            competition_item_id: 比赛单项ID
            pool_size: 小组大小
            start_time: 开始时间

        返回:
            生成的比赛列表
        """
        competition_item = CompetitionItem.objects.get(id=competition_item_id)
        participants = list(competition_item.participants.all())

        if len(participants) < 2:
            raise ValueError("参赛选手不足")

        # 按种子排序
        participants.sort(key=lambda x: x.seed or 9999)
        participant_ids = [p.id for p in participants]

        # 简单分组
        def simple_grouping(ids, size):
            """简单顺序分组"""
            groups = []
            for i in range(0, len(ids), size):
                groups.append(ids[i:i + size])
            return groups

        groups = simple_grouping(participant_ids, pool_size)

        all_matches = []

        with transaction.atomic():
            for group_idx, group in enumerate(groups):
                # 生成核心比赛对象
                core_matches = MatchGenerationAlgorithm.generate_pool_matches(
                    pool=group,
                    stage_id=competition_item_id,
                    pool_round=1,
                    start_time=start_time
                )

                # 转换为 Django 模型
                for core_match in core_matches:
                    django_match = Match.from_core(
                        core_match=core_match,
                        competition_item=competition_item,
                        save=False
                    )
                    django_match.pool_number = group_idx + 1
                    django_match.save()
                    all_matches.append(django_match)

        return all_matches

    @staticmethod
    def generate_elimination_bracket(
        competition_item_id: int,
        bracket_type: str = "single_elimination"
    ) -> List[Match]:
        """
        生成淘汰赛

        参数:
            competition_item_id: 比赛单项ID
            bracket_type: 淘汰赛类型

        返回:
            生成的比赛列表
        """
        competition_item = CompetitionItem.objects.get(id=competition_item_id)
        participant_ids = list(competition_item.participants.values_list('id', flat=True))

        if len(participant_ids) < 2:
            raise ValueError("参赛选手不足")

        # 生成核心比赛对象
        core_matches = MatchGenerationAlgorithm.generate_elimination_bracket(
            participants=participant_ids,
            stage_id=competition_item_id,
            bracket_type=bracket_type
        )

        all_matches = []

        with transaction.atomic():
            for core_match in core_matches:
                django_match = Match.from_core(
                    core_match=core_match,
                    competition_item=competition_item,
                    save=True
                )
                all_matches.append(django_match)

        return all_matches

    @staticmethod
    def generate_matches_for_competition(
        competition_item_id: int,
        match_type: str = "pool",  # "pool" 或 "elimination"
        **kwargs
    ) -> List[Match]:
        """
        为比赛生成对阵

        参数:
            competition_item_id: 比赛单项ID
            match_type: 比赛类型
            **kwargs: 其他参数

        返回:
            生成的比赛列表
        """
        if match_type == "pool":
            return MatchGenerationService.generate_pool_matches(
                competition_item_id, **kwargs
            )
        elif match_type == "elimination":
            return MatchGenerationService.generate_elimination_bracket(
                competition_item_id, **kwargs
            )
        else:
            raise ValueError(f"不支持的比赛类型: {match_type}")
