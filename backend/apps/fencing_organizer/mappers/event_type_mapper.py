from backend.apps.fencing_organizer.modules.event_type.models import DjangoEventType
from core.models.event_type import EventType


class EventTypeMapper:
    """项目类型映射器"""

    @staticmethod
    def to_domain(django_type: DjangoEventType) -> EventType:
        """Django ORM → Core Domain"""
        return EventType(
            id=django_type.id,
            type_code=django_type.type_code,
            display_name=django_type.display_name,
            weapon_type=django_type.weapon_type,
            gender=django_type.gender
        )

    @staticmethod
    def to_orm_data(event_type: EventType) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": event_type.id,
            "type_code": event_type.type_code,
            "display_name": event_type.display_name,
            "weapon_type": event_type.weapon_type,
            "gender": event_type.gender
        }
