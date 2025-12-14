from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from django.db.models import Q, Count, Avg, Min, Max
from django.db import transaction

from backend.apps.fencing_organizer.mappers.event_participant_mapper import EventParticipantMapper
from backend.apps.fencing_organizer.modules.event_participant.models import DjangoEventParticipant
from core.interfaces.event_participant_repository import EventParticipantRepositoryInterface
from core.models.event_participant import EventParticipant


class DjangoEventParticipantRepository(EventParticipantRepositoryInterface):
    """EventParticipant仓库的Django实现"""

    def get_participant_by_id(self, participant_id: UUID) -> Optional[EventParticipant]:
        """根据ID获取参与者"""
        try:
            django_participant = DjangoEventParticipant.objects.select_related(
                'event', 'fencer'
            ).get(pk=participant_id)
            return EventParticipantMapper.to_domain(django_participant)
        except DjangoEventParticipant.DoesNotExist:
            return None

    def get_participants_by_event(self, event_id: UUID, confirmed_only: bool = True) -> List[EventParticipant]:
        """获取指定项目的参与者"""
        query = DjangoEventParticipant.objects.filter(event_id=event_id)

        if confirmed_only:
            query = query.filter(is_confirmed=True)

        query = query.select_related('event', 'fencer').order_by('seed_rank', 'fencer__last_name', 'fencer__first_name')

        return [EventParticipantMapper.to_domain(p) for p in query]

    def get_participants_by_fencer(self, fencer_id: UUID) -> List[EventParticipant]:
        """获取指定运动员的参赛记录"""
        participants = DjangoEventParticipant.objects.filter(
            fencer_id=fencer_id,
            is_confirmed=True
        ).select_related('event', 'fencer').order_by('-event__start_time')

        return [EventParticipantMapper.to_domain(p) for p in participants]

    def get_participant(self, event_id: UUID, fencer_id: UUID) -> Optional[EventParticipant]:
        """获取指定项目和运动员的参与记录"""
        try:
            django_participant = DjangoEventParticipant.objects.select_related(
                'event', 'fencer'
            ).get(event_id=event_id, fencer_id=fencer_id)
            return EventParticipantMapper.to_domain(django_participant)
        except DjangoEventParticipant.DoesNotExist:
            return None

    def add_participant(self, event_id: UUID, fencer_id: UUID,
                        seed_rank: Optional[int] = None,
                        seed_value: Optional[float] = None,
                        notes: Optional[str] = None) -> EventParticipant:
        """添加参与者"""
        # 检查是否已存在
        existing = self.get_participant(event_id, fencer_id)
        if existing:
            # 如果已存在但未确认，则重新确认
            if not existing.is_confirmed:
                existing.is_confirmed = True
                existing.notes = notes or existing.notes
                return self.save_participant(existing)
            return existing

        # 创建新的参与者
        from django.utils.timezone import now
        participant = EventParticipant(
            event_id=event_id,
            fencer_id=fencer_id,
            seed_rank=seed_rank,
            seed_value=seed_value,
            notes=notes,
            is_confirmed=True,
            registration_time=now()
        )

        return self.save_participant(participant)

    def save_participant(self, participant: EventParticipant) -> EventParticipant:
        """保存或更新参与者"""
        orm_data = EventParticipantMapper.to_orm_data(participant)

        django_participant, created = DjangoEventParticipant.objects.update_or_create(
            id=participant.id,
            defaults=orm_data
        )

        return EventParticipantMapper.to_domain(django_participant)

    def remove_participant(self, event_id: UUID, fencer_id: UUID) -> bool:
        """移除参与者"""
        try:
            count, _ = DjangoEventParticipant.objects.filter(
                event_id=event_id,
                fencer_id=fencer_id
            ).delete()
            return count > 0
        except Exception:
            return False

    def update_seed_ranks(self, event_id: UUID,
                          seed_updates: List[Tuple[UUID, int]]) -> List[EventParticipant]:
        """批量更新种子排名"""
        updated_participants = []

        with transaction.atomic():
            for fencer_id, seed_rank in seed_updates:
                try:
                    participant = DjangoEventParticipant.objects.get(
                        event_id=event_id,
                        fencer_id=fencer_id
                    )
                    participant.seed_rank = seed_rank
                    participant.save()

                    updated_participants.append(EventParticipantMapper.to_domain(participant))
                except DjangoEventParticipant.DoesNotExist:
                    continue

        return updated_participants

    def get_event_stats(self, event_id: UUID) -> Dict[str, Any]:
        """获取项目统计信息"""
        stats = DjangoEventParticipant.objects.filter(event_id=event_id).aggregate(
            total_count=Count('id'),
            confirmed_count=Count('id', filter=Q(is_confirmed=True)),
            average_seed_rank=Avg('seed_rank'),
            min_seed_rank=Min('seed_rank'),
            max_seed_rank=Max('seed_rank')
        )

        # 按国家统计
        country_stats = DjangoEventParticipant.objects.filter(
            event_id=event_id,
            is_confirmed=True
        ).values('fencer__country_code').annotate(
            count=Count('id')
        ).order_by('-count')

        stats['by_country'] = [
            {'country_code': stat['fencer__country_code'], 'count': stat['count']}
            for stat in country_stats if stat['fencer__country_code']
        ]

        # 按剑种统计（从fencer获取）
        weapon_stats = DjangoEventParticipant.objects.filter(
            event_id=event_id,
            is_confirmed=True,
            fencer__primary_weapon__isnull=False
        ).values('fencer__primary_weapon').annotate(
            count=Count('id')
        ).order_by('-count')

        stats['by_weapon'] = [
            {'weapon': stat['fencer__primary_weapon'], 'count': stat['count']}
            for stat in weapon_stats if stat['fencer__primary_weapon']
        ]

        return stats

    def confirm_participant(self, event_id: UUID, fencer_id: UUID) -> Optional[EventParticipant]:
        """确认参赛"""
        try:
            participant = DjangoEventParticipant.objects.get(
                event_id=event_id,
                fencer_id=fencer_id
            )
            participant.is_confirmed = True
            participant.save()
            return EventParticipantMapper.to_domain(participant)
        except DjangoEventParticipant.DoesNotExist:
            return None

    def unconfirm_participant(self, event_id: UUID, fencer_id: UUID) -> Optional[EventParticipant]:
        """取消确认参赛"""
        try:
            participant = DjangoEventParticipant.objects.get(
                event_id=event_id,
                fencer_id=fencer_id
            )
            participant.is_confirmed = False
            participant.save()
            return EventParticipantMapper.to_domain(participant)
        except DjangoEventParticipant.DoesNotExist:
            return None

    def get_participant_count_by_event(self, event_id: UUID) -> int:
        """获取项目的参与者数量"""
        return DjangoEventParticipant.objects.filter(
            event_id=event_id,
            is_confirmed=True
        ).count()

    def get_top_seeded_fencers(self, event_id: UUID, limit: int = 10) -> List[EventParticipant]:
        """获取种子排名最高的参与者"""
        participants = DjangoEventParticipant.objects.filter(
            event_id=event_id,
            is_confirmed=True,
            seed_rank__isnull=False
        ).order_by('seed_rank')[:limit]

        return [EventParticipantMapper.to_domain(p) for p in participants]

    def get_participants_with_details(self, event_id: UUID) -> List[Dict[str, Any]]:
        """获取参与者详细信息"""
        participants = DjangoEventParticipant.objects.filter(
            event_id=event_id,
            is_confirmed=True
        ).select_related('fencer').order_by('seed_rank')

        result = []
        for participant in participants:
            result.append({
                'participant': EventParticipantMapper.to_domain(participant),
                'fencer': {
                    'id': participant.fencer.id,
                    'display_name': participant.fencer.display_name,
                    'country_code': participant.fencer.country_code,
                    'current_ranking': participant.fencer.current_ranking,
                    'primary_weapon': participant.fencer.primary_weapon
                }
            })

        return result
