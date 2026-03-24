from backend.apps.fencing_organizer.modules.event.models import DjangoEvent
from core.models.event import Event


class EventMapper:
    """比赛项目映射器"""

    @staticmethod
    def to_domain(django_event: DjangoEvent) -> Event:
        """Django ORM → Core Domain"""
        return Event(
            id=django_event.id,
            tournament_id=django_event.tournament_id,
            rule_id=django_event.rule_id,
            event_type=django_event.event_type,
            status=django_event.status,
            current_step=django_event.current_step,
            live_ranking=django_event.live_ranking,
            de_trees=django_event.de_trees,
            custom_rule_config=django_event.custom_rule_config,
            event_name=django_event.event_name,
            is_team_event=django_event.is_team_event,
            start_time=django_event.start_time,
            created_at=django_event.created_at,
            updated_at=django_event.updated_at,
        )

    @staticmethod
    def to_orm_data(event: Event) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": event.id,
            "tournament_id": event.tournament_id,
            "rule_id": event.rule_id,
            "event_type": event.event_type,
            "status": event.status,
            "current_step": event.current_step,
            "live_ranking": event.live_ranking,
            "de_trees": event.de_trees,
            "custom_rule_config": event.custom_rule_config,
            "event_name": event.event_name,
            "is_team_event": event.is_team_event,
            "start_time": event.start_time,
        }
