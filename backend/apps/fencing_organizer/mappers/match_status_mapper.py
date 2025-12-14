from backend.apps.fencing_organizer.modules.match_status.models import DjangoMatchStatusType
from core.models.match_status_type import MatchStatusType


class MatchStatusMapper:
    """比赛状态映射器"""

    @staticmethod
    def to_domain(django_status: DjangoMatchStatusType) -> MatchStatusType:
        """Django ORM → Core Domain"""
        return MatchStatusType(
            id=django_status.id,
            status_code=django_status.status_code,
            description=django_status.description
        )

    @staticmethod
    def to_orm_data(match_status: MatchStatusType) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": match_status.id,
            "status_code": match_status.status_code,
            "description": match_status.description
        }
