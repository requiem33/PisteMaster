from dataclasses import dataclass, field
from enum import Enum
from typing import List

from core.models.competitionitem import CompetitionItem
from core.models.enums import EventType


class CompetitionStatus(Enum):
    DRAFT = 'draft'      # 草稿
    OPEN = 'open'        # 报名中
    CLOSED = 'closed'    # 报名截止
    ONGOING = 'ongoing'  # 进行中
    COMPLETED = 'completed' # 已结束
    CANCELLED = 'cancelled' # 已取消


@dataclass
class TournamentEvent:
    """赛事单元：个人赛或团体赛"""
    name: str  # 如 "个人赛", "团体赛"
    type: EventType
    items: List[CompetitionItem] = field(default_factory=list)

    def add_item(self, item: CompetitionItem) -> None:
        """添加比赛单项"""
        # 验证类型一致性：个人赛只能包含个人项目等
        if (self.type == EventType.INDIVIDUAL and item.team_ids) or \
                (self.type == EventType.TEAM and item.participant_ids):
            raise ValueError(f"比赛单项类型与{self.type.value}类型不匹配")
        self.items.append(item)
