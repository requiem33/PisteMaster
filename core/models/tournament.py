from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional, Set
from .enums import TournamentStatus, EventType
from .tournamentevent import TournamentEvent
from .competitionitem import CompetitionItem


@dataclass
class Tournament:
    """赛事主容器"""
    name: str
    start_date: date
    end_date: Optional[date] = None
    location: str = ""
    status: TournamentStatus = TournamentStatus.DRAFT

    # 包含的赛事单元
    events: List[TournamentEvent] = field(default_factory=list)

    # 系统字段
    id: Optional[int] = field(default=None, compare=False)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def duration_days(self) -> int:
        """计算赛事持续天数"""
        end = self.end_date or self.start_date
        return (end - self.start_date).days + 1

    @property
    def all_competition_items(self) -> List[CompetitionItem]:
        """获取所有比赛单项（扁平化列表）"""
        items = []
        for event in self.events:
            items.extend(event.items)
        return items

    def add_event(self, event: TournamentEvent) -> None:
        """添加赛事单元"""
        self.events.append(event)

    def find_event_by_type(self, event_type: EventType) -> List[TournamentEvent]:
        """查找特定类型的赛事单元"""
        return [event for event in self.events if event.type == event_type]

    def get_participating_fencers(self) -> Set[int]:
        """获取所有参赛选手ID（去重）"""
        fencer_ids = set()
        for item in self.all_competition_items:
            fencer_ids.update(item.participant_ids)
        return fencer_ids
