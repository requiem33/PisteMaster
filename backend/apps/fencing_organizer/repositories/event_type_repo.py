from typing import Optional, List
from uuid import UUID

from backend.apps.fencing_organizer.mappers.event_type_mapper import EventTypeMapper
from backend.apps.fencing_organizer.modules.event_type.models import DjangoEventType
from core.models.event_type import EventType


class DjangoEventTypeRepository:
    """项目类型仓库"""

    def get_by_id(self, type_id: UUID) -> Optional[EventType]:
        """通过ID获取类型"""
        try:
            django_type = DjangoEventType.objects.get(pk=type_id)
            return EventTypeMapper.to_domain(django_type)
        except DjangoEventType.DoesNotExist:
            return None

    def get_by_code(self, type_code: str) -> Optional[EventType]:
        """通过代码获取类型"""
        try:
            django_type = DjangoEventType.objects.get(type_code=type_code)
            return EventTypeMapper.to_domain(django_type)
        except DjangoEventType.DoesNotExist:
            return None

    def get_by_weapon_and_gender(self, weapon_type: str, gender: str) -> List[EventType]:
        """通过剑种和性别获取类型"""
        django_types = DjangoEventType.objects.filter(
            weapon_type=weapon_type,
            gender=gender
        ).order_by('type_code')

        return [EventTypeMapper.to_domain(t) for t in django_types]

    def get_individual_types(self) -> List[EventType]:
        """获取所有个人赛类型"""
        django_types = DjangoEventType.objects.filter(type_code__contains='INDIVIDUAL').order_by('type_code')
        return [EventTypeMapper.to_domain(t) for t in django_types]

    def get_team_types(self) -> List[EventType]:
        """获取所有团体赛类型"""
        django_types = DjangoEventType.objects.filter(type_code__contains='TEAM').order_by('type_code')
        return [EventTypeMapper.to_domain(t) for t in django_types]

    def get_all(self) -> List[EventType]:
        """获取所有类型"""
        django_types = DjangoEventType.objects.all().order_by('type_code')
        return [EventTypeMapper.to_domain(t) for t in django_types]

    def save(self, event_type: EventType) -> EventType:
        """保存项目类型"""
        orm_data = EventTypeMapper.to_orm_data(event_type)

        django_type, created = DjangoEventType.objects.update_or_create(
            id=event_type.id,
            defaults=orm_data
        )

        return EventTypeMapper.to_domain(django_type)
