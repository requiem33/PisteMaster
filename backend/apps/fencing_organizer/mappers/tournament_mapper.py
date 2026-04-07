from core.models.mapper_base import versioned_fields_to_dict, versioned_fields_from_dict
from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament
from core.models.tournament import Tournament


class TournamentMapper:
    """赛事映射器"""

    @staticmethod
    def to_domain(django_tournament: DjangoTournament) -> Tournament:
        """Django ORM → Core Domain"""
        created_by_id = None
        if django_tournament.created_by:
            created_by_id = django_tournament.created_by.id

        scheduler_ids = list(django_tournament.schedulers.values_list("id", flat=True))
        version_fields = versioned_fields_to_dict(django_tournament)

        return Tournament(
            id=django_tournament.id,
            tournament_name=django_tournament.tournament_name,
            start_date=django_tournament.start_date,
            end_date=django_tournament.end_date,
            status=django_tournament.status,
            organizer=django_tournament.organizer,
            location=django_tournament.location,
            created_by_id=created_by_id,
            scheduler_ids=scheduler_ids,
            created_at=django_tournament.created_at,
            updated_at=django_tournament.updated_at,
            **version_fields
        )

    @staticmethod
    def to_orm_data(tournament: Tournament) -> dict:
        """Core Domain → ORM数据字典"""
        data = {
            "id": tournament.id,
            "tournament_name": tournament.tournament_name,
            "start_date": tournament.start_date,
            "end_date": tournament.end_date,
            "status": tournament.status,
            "organizer": tournament.organizer,
            "location": tournament.location,
            "created_by_id": tournament.created_by_id,
        }
        versioned_fields_from_dict(tournament.__dict__, data)
        return data

    @staticmethod
    def apply_schedulers(django_tournament: DjangoTournament, scheduler_ids: list) -> None:
        """Apply scheduler IDs to Django tournament (ManyToMany field)"""
        if scheduler_ids is not None:
            from backend.apps.users.models import User

            django_tournament.schedulers.set(User.objects.filter(id__in=scheduler_ids))
