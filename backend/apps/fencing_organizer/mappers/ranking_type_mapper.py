from backend.apps.fencing_organizer.modules.ranking_type.models import DjangoRankingType
from core.models.ranking_type import RankingType


class RankingTypeMapper:
    """排名类型映射器"""

    @staticmethod
    def to_domain(django_type: DjangoRankingType) -> RankingType:
        """Django ORM → Core Domain"""
        return RankingType(
            id=django_type.id,
            type_code=django_type.type_code,
            display_name=django_type.display_name
        )

    @staticmethod
    def to_orm_data(ranking_type: RankingType) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": ranking_type.id,
            "type_code": ranking_type.type_code,
            "display_name": ranking_type.display_name
        }
