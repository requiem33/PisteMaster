from backend.apps.fencing_organizer.modules.tournament_status.models import DjangoTournamentStatus
from core.models.tournament_status import TournamentStatus


class TournamentStatusMapper:
    """赛事状态映射器"""

    @staticmethod
    def to_domain(django_status: DjangoTournamentStatus) -> TournamentStatus:
        """Django ORM → Core Domain"""
        return TournamentStatus(
            id=django_status.id,
            status_code=django_status.status_code,
            display_name=django_status.display_name,
            description=django_status.description
        )

    @staticmethod
    def to_orm_data(status: TournamentStatus) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": status.id,
            "status_code": status.status_code,
            "display_name": status.display_name,
            "description": status.description
        }
