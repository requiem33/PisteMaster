from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from core.models.event import Event


class EventRepositoryInterface(ABC):
    """比赛项目仓库接口"""

    @abstractmethod
    def get_event_by_id(self, event_id: UUID) -> Optional[Event]:
        pass

    @abstractmethod
    def get_events_by_tournament(self, tournament_id: UUID) -> List[Event]:
        pass

    @abstractmethod
    def get_events_by_type(self, event_type_id: UUID) -> List[Event]:
        pass

    @abstractmethod
    def get_events_by_status(self, status_id: UUID) -> List[Event]:
        pass

    @abstractmethod
    def get_upcoming_events(self, start_date: datetime, end_date: datetime) -> List[Event]:
        pass

    @abstractmethod
    def get_all_events(self) -> List[Event]:
        pass

    @abstractmethod
    def save_event(self, event: Event) -> Event:
        pass

    @abstractmethod
    def delete_event(self, event_id: UUID) -> bool:
        pass
