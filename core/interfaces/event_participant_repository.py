from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from core.models.event_participant import EventParticipant


class EventParticipantRepositoryInterface(ABC):
    """EventParticipant仓库接口"""

    @abstractmethod
    def get_participant_by_id(self, participant_id: UUID) -> Optional[EventParticipant]:
        """根据ID获取参与者"""
        pass

    @abstractmethod
    def get_participants_by_event(self, event_id: UUID, confirmed_only: bool = True) -> List[EventParticipant]:
        """获取指定项目的参与者"""
        pass

    @abstractmethod
    def get_participants_by_fencer(self, fencer_id: UUID) -> List[EventParticipant]:
        """获取指定运动员的参赛记录"""
        pass

    @abstractmethod
    def get_participant(self, event_id: UUID, fencer_id: UUID) -> Optional[EventParticipant]:
        """获取指定项目和运动员的参与记录"""
        pass

    @abstractmethod
    def add_participant(self, event_id: UUID, fencer_id: UUID,
                        seed_rank: Optional[int] = None,
                        seed_value: Optional[float] = None,
                        notes: Optional[str] = None) -> EventParticipant:
        """添加参与者"""
        pass

    @abstractmethod
    def save_participant(self, participant: EventParticipant) -> EventParticipant:
        """保存或更新参与者"""
        pass

    @abstractmethod
    def remove_participant(self, event_id: UUID, fencer_id: UUID) -> bool:
        """移除参与者"""
        pass

    @abstractmethod
    def update_seed_ranks(self, event_id: UUID,
                          seed_updates: List[Tuple[UUID, int]]) -> List[EventParticipant]:
        """批量更新种子排名"""
        pass

    @abstractmethod
    def get_event_stats(self, event_id: UUID) -> Dict[str, Any]:
        """获取项目统计信息"""
        pass

    @abstractmethod
    def confirm_participant(self, event_id: UUID, fencer_id: UUID) -> Optional[EventParticipant]:
        """确认参赛"""
        pass

    @abstractmethod
    def unconfirm_participant(self, event_id: UUID, fencer_id: UUID) -> Optional[EventParticipant]:
        """取消确认参赛"""
        pass

    @abstractmethod
    def get_participant_count_by_event(self, event_id: UUID) -> int:
        """获取项目的参与者数量"""
        pass

    @abstractmethod
    def get_top_seeded_fencers(self, event_id: UUID, limit: int = 10) -> List[EventParticipant]:
        """获取种子排名最高的参与者"""
        pass
