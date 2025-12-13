from typing import Optional, List
from uuid import UUID

from backend.apps.fencing_organizer.mappers.ranking_type_mapper import RankingTypeMapper
from backend.apps.fencing_organizer.modules.ranking_type.models import DjangoRankingType
from core.models.ranking_type import RankingType


class DjangoRankingTypeRepository:
    """排名类型仓库"""

    def get_by_id(self, type_id: UUID) -> Optional[RankingType]:
        """通过ID获取排名类型"""
        try:
            django_type = DjangoRankingType.objects.get(pk=type_id)
            return RankingTypeMapper.to_domain(django_type)
        except DjangoRankingType.DoesNotExist:
            return None

    def get_by_code(self, type_code: str) -> Optional[RankingType]:
        """通过代码获取排名类型"""
        try:
            django_type = DjangoRankingType.objects.get(type_code=type_code)
            return RankingTypeMapper.to_domain(django_type)
        except DjangoRankingType.DoesNotExist:
            return None

    def get_all(self) -> List[RankingType]:
        """获取所有排名类型"""
        django_types = DjangoRankingType.objects.all().order_by('type_code')
        return [RankingTypeMapper.to_domain(t) for t in django_types]

    def save(self, ranking_type: RankingType) -> RankingType:
        """保存排名类型"""
        orm_data = RankingTypeMapper.to_orm_data(ranking_type)

        django_type, created = DjangoRankingType.objects.update_or_create(
            id=ranking_type.id,
            defaults=orm_data
        )

        return RankingTypeMapper.to_domain(django_type)
