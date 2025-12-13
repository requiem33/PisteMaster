from typing import Optional, List
from uuid import UUID

from backend.apps.fencing_organizer.mappers.event_status_mapper import EventStatusMapper
from backend.apps.fencing_organizer.modules.event_status.models import DjangoEventStatus
from core.models.event_status import EventStatus


class DjangoEventStatusRepository:
    """项目状态仓库"""

    def get_by_id(self, status_id: UUID) -> Optional[EventStatus]:
        """通过ID获取状态"""
        try:
            django_status = DjangoEventStatus.objects.get(pk=status_id)
            return EventStatusMapper.to_domain(django_status)
        except DjangoEventStatus.DoesNotExist:
            return None

    def get_by_code(self, status_code: str) -> Optional[EventStatus]:
        """通过代码获取状态"""
        try:
            django_status = DjangoEventStatus.objects.get(status_code=status_code)
            return EventStatusMapper.to_domain(django_status)
        except DjangoEventStatus.DoesNotExist:
            return None

    def get_all(self) -> List[EventStatus]:
        """获取所有状态"""
        django_statuses = DjangoEventStatus.objects.all().order_by('status_code')
        return [EventStatusMapper.to_domain(s) for s in django_statuses]

    def save(self, event_status: EventStatus) -> EventStatus:
        """保存项目状态"""
        orm_data = EventStatusMapper.to_orm_data(event_status)

        django_status, created = DjangoEventStatus.objects.update_or_create(
            id=event_status.id,
            defaults=orm_data
        )

        return EventStatusMapper.to_domain(django_status)
