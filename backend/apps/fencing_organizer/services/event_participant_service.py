from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime
from django.db import IntegrityError
from django.utils.timezone import now

from core.models.event_participant import EventParticipant
from backend.apps.fencing_organizer.repositories.event_participant_repo import DjangoEventParticipantRepository
from backend.apps.fencing_organizer.repositories.event_repo import DjangoEventRepository
from backend.apps.fencing_organizer.repositories.fencer_repo import DjangoFencerRepository


class EventParticipantService:
    """EventParticipant业务服务"""

    def __init__(self,
                 participant_repository: Optional[DjangoEventParticipantRepository] = None,
                 event_repository: Optional[DjangoEventRepository] = None,
                 fencer_repository: Optional[DjangoFencerRepository] = None):

        self.participant_repository = participant_repository or DjangoEventParticipantRepository()
        self.event_repository = event_repository or DjangoEventRepository()
        self.fencer_repository = fencer_repository or DjangoFencerRepository()

    def register_fencer_to_event(self, event_id: UUID, fencer_id: UUID,
                                 seed_rank: Optional[int] = None,
                                 seed_value: Optional[float] = None,
                                 notes: Optional[str] = None) -> EventParticipant:
        """将运动员注册到项目"""
        # 验证事件存在
        event = self.event_repository.get_event_by_id(event_id)
        if not event:
            raise self.EventParticipantServiceError(f"项目 {event_id} 不存在")

        # 验证运动员存在
        fencer = self.fencer_repository.get_fencer_by_id(fencer_id)
        if not fencer:
            raise self.EventParticipantServiceError(f"运动员 {fencer_id} 不存在")

        # 验证运动员性别与项目要求（如果有）
        if event.gender and fencer.gender and event.gender != 'MIXED' and event.gender != 'OPEN':
            if event.gender != fencer.gender:
                raise self.EventParticipantServiceError(
                    f"运动员性别 {fencer.gender} 与项目要求 {event.gender} 不匹配"
                )

        # 添加参与者
        try:
            participant = self.participant_repository.add_participant(
                event_id, fencer_id, seed_rank, seed_value, notes
            )
            return participant
        except IntegrityError as e:
            if 'unique_event_fencer' in str(e):
                # 已经注册，返回现有记录
                existing = self.participant_repository.get_participant(event_id, fencer_id)
                if existing:
                    return existing
            raise self.EventParticipantServiceError(f"注册失败: {str(e)}")

    def bulk_register_fencers(self, event_id: UUID, fencer_ids: List[UUID]) -> Tuple[
        List[EventParticipant], List[UUID]]:
        """批量注册运动员到项目"""
        successful = []
        failed = []

        for fencer_id in fencer_ids:
            try:
                participant = self.register_fencer_to_event(event_id, fencer_id)
                successful.append(participant)
            except self.EventParticipantServiceError as e:
                failed.append(fencer_id)

        return successful, failed

    def remove_fencer_from_event(self, event_id: UUID, fencer_id: UUID) -> bool:
        """从项目中移除运动员"""
        # 检查参与者是否存在
        participant = self.participant_repository.get_participant(event_id, fencer_id)
        if not participant:
            return False

        # 检查是否已经开始比赛（如果有比赛记录则不能删除）
        # 这里可以添加更复杂的检查逻辑

        return self.participant_repository.remove_participant(event_id, fencer_id)

    def update_seed_ranking(self, event_id: UUID, seed_updates: List[Dict[str, Any]]) -> List[EventParticipant]:
        """更新种子排名"""
        # 验证种子排名数据
        validated_updates = []
        for update in seed_updates:
            fencer_id = update.get('fencer_id')
            seed_rank = update.get('seed_rank')

            if not fencer_id or seed_rank is None:
                continue

            # 验证运动员是否参与了该项目
            participant = self.participant_repository.get_participant(event_id, fencer_id)
            if not participant:
                continue

            validated_updates.append((fencer_id, seed_rank))

        if not validated_updates:
            raise self.EventParticipantServiceError("没有有效的种子排名更新")

        return self.participant_repository.update_seed_ranks(event_id, validated_updates)

    def get_event_participants(self, event_id: UUID, confirmed_only: bool = True) -> List[EventParticipant]:
        """获取项目参与者列表"""
        return self.participant_repository.get_participants_by_event(event_id, confirmed_only)

    def get_fencer_events(self, fencer_id: UUID) -> List[EventParticipant]:
        """获取运动员的参赛记录"""
        return self.participant_repository.get_participants_by_fencer(fencer_id)

    def get_event_stats(self, event_id: UUID) -> Dict[str, Any]:
        """获取项目统计信息"""
        return self.participant_repository.get_event_stats(event_id)

    def confirm_participation(self, event_id: UUID, fencer_id: UUID) -> Optional[EventParticipant]:
        """确认参赛"""
        return self.participant_repository.confirm_participant(event_id, fencer_id)

    def unconfirm_participation(self, event_id: UUID, fencer_id: UUID) -> Optional[EventParticipant]:
        """取消确认参赛"""
        return self.participant_repository.unconfirm_participant(event_id, fencer_id)

    def generate_seed_ranking(self, event_id: UUID,
                              based_on: str = 'world_ranking') -> List[EventParticipant]:
        """生成种子排名"""
        participants = self.get_event_participants(event_id)

        if not participants:
            raise self.EventParticipantServiceError("项目没有参与者")

        # 根据不同的依据生成种子排名
        if based_on == 'world_ranking':
            # 按世界排名排序
            sorted_participants = sorted(
                participants,
                key=lambda p: p.seed_value or self._get_fencer_ranking(p.fencer_id) or float('inf')
            )
        elif based_on == 'registration_time':
            # 按报名时间排序
            sorted_participants = sorted(
                participants,
                key=lambda p: p.registration_time or datetime.min
            )
        else:
            # 默认随机排序
            import random
            sorted_participants = list(participants)
            random.shuffle(sorted_participants)

        # 更新种子排名
        seed_updates = []
        for i, participant in enumerate(sorted_participants, 1):
            seed_updates.append({
                'fencer_id': participant.fencer_id,
                'seed_rank': i
            })

        return self.update_seed_ranking(event_id, seed_updates)

    def _get_fencer_ranking(self, fencer_id: UUID) -> Optional[int]:
        """获取运动员排名"""
        fencer = self.fencer_repository.get_fencer_by_id(fencer_id)
        return fencer.current_ranking if fencer else None

    class EventParticipantServiceError(Exception):
        """Service层异常"""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
