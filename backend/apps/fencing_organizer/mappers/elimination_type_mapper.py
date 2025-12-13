from backend.apps.fencing_organizer.modules.elimination_type.models import DjangoEliminationType
from core.models.elimination_type import EliminationType


class EliminationTypeMapper:
    """淘汰赛类型映射器"""

    @staticmethod
    def to_domain(django_type: DjangoEliminationType) -> EliminationType:
        """Django ORM → Core Domain"""
        return EliminationType(
            id=django_type.id,
            type_code=django_type.type_code,
            display_name=django_type.display_name
        )

    @staticmethod
    def to_orm_data(elimination_type: EliminationType) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": elimination_type.id,
            "type_code": elimination_type.type_code,
            "display_name": elimination_type.display_name
        }