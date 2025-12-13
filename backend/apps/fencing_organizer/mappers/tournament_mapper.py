from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament
from core.models.tournament import Tournament


class TournamentMapper:
    """赛事映射器"""

    @staticmethod
    def to_domain(django_tournament: DjangoTournament) -> Tournament:
        """Django ORM → Core Domain"""
        return Tournament(
            id=django_tournament.id,
            tournament_name=django_tournament.tournament_name,
            start_date=django_tournament.start_date,
            end_date=django_tournament.end_date,
            status_id=django_tournament.status.id,
            organizer=django_tournament.organizer,
            location=django_tournament.location,
            created_at=django_tournament.created_at,
            updated_at=django_tournament.updated_at
        )

    @staticmethod
    def to_orm_data(tournament: Tournament) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": tournament.id,
            "tournament_name": tournament.tournament_name,
            "start_date": tournament.start_date,
            "end_date": tournament.end_date,
            "status_id": tournament.status_id,
            "organizer": tournament.organizer,
            "location": tournament.location
            # 注意：created_at和updated_at不包含在这里，让Django自动处理
        }
