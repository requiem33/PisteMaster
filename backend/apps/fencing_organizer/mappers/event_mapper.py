from backend.apps.fencing_organizer.modules.event.models import DjangoEvent
from core.models.event import Event


class EventMapper:
    """比赛项目映射器"""

    @staticmethod
    def to_domain(django_event: DjangoEvent) -> Event:
        """Django ORM → Core Domain"""
        return Event(
            id=django_event.id,
            tournament_id=django_event.tournament.id,
            rule_id=django_event.rule.id,
            event_type_id=django_event.event_type.id,
            status_id=django_event.status.id,
            event_name=django_event.event_name,
            is_team_event=django_event.is_team_event,
            start_time=django_event.start_time,
            created_at=django_event.created_at,
            updated_at=django_event.updated_at
        )

    @staticmethod
    def to_orm_data(event: Event) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": event.id,
            "tournament_id": event.tournament_id,
            "rule_id": event.rule_id,
            "event_type_id": event.event_type_id,
            "status_id": event.status_id,
            "event_name": event.event_name,
            "is_team_event": event.is_team_event,
            "start_time": event.start_time
            # 注意：created_at和updated_at不包含在这里，让Django自动处理
        }
