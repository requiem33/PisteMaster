from backend.apps.fencing_organizer.modules.event_participant.models import DjangoEventParticipant
from core.models.event_participant import EventParticipant


class EventParticipantMapper:
    """EventParticipant映射器"""

    @staticmethod
    def to_domain(django_participant: DjangoEventParticipant) -> EventParticipant:
        """Django ORM → Core Domain"""
        return EventParticipant(
            id=django_participant.id,
            event_id=django_participant.event.id,
            fencer_id=django_participant.fencer.id,
            seed_rank=django_participant.seed_rank,
            seed_value=django_participant.seed_value,
            is_confirmed=django_participant.is_confirmed,
            registration_time=django_participant.registration_time,
            notes=django_participant.notes,
            created_at=django_participant.created_at,
            updated_at=django_participant.updated_at
        )

    @staticmethod
    def to_orm_data(participant: EventParticipant) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": participant.id,
            "event_id": participant.event_id,
            "fencer_id": participant.fencer_id,
            "seed_rank": participant.seed_rank,
            "seed_value": participant.seed_value,
            "is_confirmed": participant.is_confirmed,
            "registration_time": participant.registration_time,
            "notes": participant.notes,
            "created_at": participant.created_at,
            "updated_at": participant.updated_at
        }
