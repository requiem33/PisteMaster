from backend.apps.fencing_organizer.modules.event_status.models import DjangoEventStatus
from core.models.event_status import EventStatus


class EventStatusMapper:
    """项目状态映射器"""

    @staticmethod
    def to_domain(django_status: DjangoEventStatus) -> EventStatus:
        """Django ORM → Core Domain"""
        return EventStatus(
            id=django_status.id,
            status_code=django_status.status_code,
            display_name=django_status.display_name
        )

    @staticmethod
    def to_orm_data(event_status: EventStatus) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": event_status.id,
            "status_code": event_status.status_code,
            "display_name": event_status.display_name
        }
