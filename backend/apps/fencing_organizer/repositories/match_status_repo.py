from typing import Optional, List
from uuid import UUID

from backend.apps.fencing_organizer.mappers.match_status_mapper import MatchStatusMapper
from backend.apps.fencing_organizer.modules.match_status.models import DjangoMatchStatusType
from core.models.match_status_type import MatchStatusType


class DjangoMatchStatusRepository:
    """比赛状态仓库"""

    def get_by_id(self, status_id: UUID) -> Optional[MatchStatusType]:
        """通过ID获取状态"""
        try:
            django_status = DjangoMatchStatusType.objects.get(pk=status_id)
            return MatchStatusMapper.to_domain(django_status)
        except DjangoMatchStatusType.DoesNotExist:
            return None

    def get_by_code(self, status_code: str) -> Optional[MatchStatusType]:
        """通过代码获取状态"""
        try:
            django_status = DjangoMatchStatusType.objects.get(status_code=status_code)
            return MatchStatusMapper.to_domain(django_status)
        except DjangoMatchStatusType.DoesNotExist:
            return None

    def get_all(self) -> List[MatchStatusType]:
        """获取所有状态"""
        django_statuses = DjangoMatchStatusType.objects.all().order_by('status_code')
        return [MatchStatusMapper.to_domain(s) for s in django_statuses]

    def save(self, match_status: MatchStatusType) -> MatchStatusType:
        """保存比赛状态"""
        orm_data = MatchStatusMapper.to_orm_data(match_status)

        django_status, created = DjangoMatchStatusType.objects.update_or_create(
            id=match_status.id,
            defaults=orm_data
        )

        return MatchStatusMapper.to_domain(django_status)
