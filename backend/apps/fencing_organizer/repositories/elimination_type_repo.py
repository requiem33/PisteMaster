from typing import Optional, List
from uuid import UUID

from backend.apps.fencing_organizer.mappers.elimination_type_mapper import EliminationTypeMapper
from backend.apps.fencing_organizer.modules.elimination_type.models import DjangoEliminationType
from core.models.elimination_type import EliminationType


class DjangoEliminationTypeRepository:
    """淘汰赛类型仓库"""

    def get_by_id(self, type_id: UUID) -> Optional[EliminationType]:
        """通过ID获取淘汰赛类型"""
        try:
            django_type = DjangoEliminationType.objects.get(pk=type_id)
            return EliminationTypeMapper.to_domain(django_type)
        except DjangoEliminationType.DoesNotExist:
            return None

    def get_by_code(self, type_code: str) -> Optional[EliminationType]:
        """通过代码获取淘汰赛类型"""
        try:
            django_type = DjangoEliminationType.objects.get(type_code=type_code)
            return EliminationTypeMapper.to_domain(django_type)
        except DjangoEliminationType.DoesNotExist:
            return None

    def get_all(self) -> List[EliminationType]:
        """获取所有淘汰赛类型"""
        django_types = DjangoEliminationType.objects.all().order_by('type_code')
        return [EliminationTypeMapper.to_domain(t) for t in django_types]

    def save(self, elimination_type: EliminationType) -> EliminationType:
        """保存淘汰赛类型"""
        orm_data = EliminationTypeMapper.to_orm_data(elimination_type)

        django_type, created = DjangoEliminationType.objects.update_or_create(
            id=elimination_type.id,
            defaults=orm_data
        )

        return EliminationTypeMapper.to_domain(django_type)
