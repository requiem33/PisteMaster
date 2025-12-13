from typing import Optional, List
from uuid import UUID
from datetime import datetime
from django.db.models import Q

from backend.apps.fencing_organizer.mappers.event_mapper import EventMapper
from backend.apps.fencing_organizer.modules.event.models import DjangoEvent
from core.interfaces.event_repository import EventRepositoryInterface
from core.models.event import Event


class DjangoEventRepository(EventRepositoryInterface):
    """比赛项目仓库的Django实现"""

    def get_event_by_id(self, event_id: UUID) -> Optional[Event]:
        """通过ID获取项目"""
        try:
            django_event = DjangoEvent.objects.select_related(
                'tournament', 'rule', 'event_type', 'status'
            ).get(pk=event_id)
            return EventMapper.to_domain(django_event)
        except DjangoEvent.DoesNotExist:
            return None

    def get_events_by_tournament(self, tournament_id: UUID) -> List[Event]:
        """获取指定赛事的项目"""
        django_events = DjangoEvent.objects.select_related(
            'tournament', 'rule', 'event_type', 'status'
        ).filter(
            tournament_id=tournament_id
        ).order_by('start_time', 'event_name')

        return [EventMapper.to_domain(e) for e in django_events]

    def get_events_by_type(self, event_type_id: UUID) -> List[Event]:
        """获取指定类型的项目"""
        django_events = DjangoEvent.objects.select_related(
            'tournament', 'rule', 'event_type', 'status'
        ).filter(
            event_type_id=event_type_id
        ).order_by('-start_time')

        return [EventMapper.to_domain(e) for e in django_events]

    def get_events_by_status(self, status_id: UUID) -> List[Event]:
        """获取指定状态的项目"""
        django_events = DjangoEvent.objects.select_related(
            'tournament', 'rule', 'event_type', 'status'
        ).filter(
            status_id=status_id
        ).order_by('start_time')

        return [EventMapper.to_domain(e) for e in django_events]

    def get_upcoming_events(self, start_date: datetime, end_date: datetime) -> List[Event]:
        """获取指定时间范围内的项目"""
        django_events = DjangoEvent.objects.select_related(
            'tournament', 'rule', 'event_type', 'status'
        ).filter(
            Q(start_time__gte=start_date) & Q(start_time__lte=end_date)
        ).order_by('start_time')

        return [EventMapper.to_domain(e) for e in django_events]

    def get_all_events(self) -> List[Event]:
        """获取所有项目"""
        django_events = DjangoEvent.objects.select_related(
            'tournament', 'rule', 'event_type', 'status'
        ).all().order_by('-start_time')

        return [EventMapper.to_domain(e) for e in django_events]

    def save_event(self, event: Event) -> Event:
        """保存或更新项目"""
        orm_data = EventMapper.to_orm_data(event)

        django_event, created = DjangoEvent.objects.update_or_create(
            id=event.id,
            defaults=orm_data
        )

        return EventMapper.to_domain(django_event)

    def delete_event(self, event_id: UUID) -> bool:
        """删除项目"""
        try:
            # 检查是否有相关数据（如小组、比赛等）
            # 这里可以添加更复杂的检查逻辑
            count, _ = DjangoEvent.objects.filter(id=event_id).delete()
            return count > 0
        except Exception:
            return False

    def search_events(self, **filters) -> List[Event]:
        """搜索项目"""
        queryset = DjangoEvent.objects.select_related(
            'tournament', 'rule', 'event_type', 'status'
        )

        # 应用过滤器
        if 'tournament_id' in filters:
            queryset = queryset.filter(tournament_id=filters['tournament_id'])
        if 'tournament_name' in filters:
            queryset = queryset.filter(tournament__tournament_name__icontains=filters['tournament_name'])
        if 'event_name' in filters:
            queryset = queryset.filter(event_name__icontains=filters['event_name'])
        if 'event_type_code' in filters:
            queryset = queryset.filter(event_type__type_code=filters['event_type_code'])
        if 'status_code' in filters:
            queryset = queryset.filter(status__status_code=filters['status_code'])
        if 'weapon_type' in filters:
            queryset = queryset.filter(event_type__weapon_type=filters['weapon_type'])
        if 'gender' in filters:
            queryset = queryset.filter(event_type__gender=filters['gender'])
        if 'is_team_event' in filters:
            queryset = queryset.filter(is_team_event=filters['is_team_event'])
        if 'date_range' in filters:
            start_date, end_date = filters['date_range']
            queryset = queryset.filter(
                Q(start_time__gte=start_date) & Q(start_time__lte=end_date)
            )
        if 'is_active' in filters:
            if filters['is_active']:
                queryset = queryset.exclude(status__status_code='COMPLETED').exclude(status__status_code='CANCELLED')
            else:
                queryset = queryset.filter(status__status_code__in=['COMPLETED', 'CANCELLED'])

        # 排序
        ordering = filters.get('ordering', '-start_time')
        if ordering:
            queryset = queryset.order_by(ordering)

        return [EventMapper.to_domain(e) for e in queryset]
