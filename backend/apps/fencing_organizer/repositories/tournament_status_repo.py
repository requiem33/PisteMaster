from typing import Optional, List
from uuid import UUID

from backend.apps.fencing_organizer.mappers.tournament_status_mapper import TournamentStatusMapper
from backend.apps.fencing_organizer.modules.tournament_status.models import DjangoTournamentStatus
from core.interfaces.tournament_status_repository import TournamentStatusRepositoryInterface
from core.models.tournament_status import TournamentStatus


class DjangoTournamentStatusRepository(TournamentStatusRepositoryInterface):
    """赛事状态仓库的Django实现"""

    def get_status_by_id(self, status_id: UUID) -> Optional[TournamentStatus]:
        """通过ID获取状态"""
        try:
            django_status = DjangoTournamentStatus.objects.get(pk=status_id)
            return TournamentStatusMapper.to_domain(django_status)
        except DjangoTournamentStatus.DoesNotExist:
            return None

    def get_status_by_code(self, status_code: str) -> Optional[TournamentStatus]:
        """通过状态代码获取状态"""
        try:
            django_status = DjangoTournamentStatus.objects.get(status_code=status_code)
            return TournamentStatusMapper.to_domain(django_status)
        except DjangoTournamentStatus.DoesNotExist:
            return None

    def get_all_statuses(self) -> List[TournamentStatus]:
        """获取所有状态"""
        django_statuses = DjangoTournamentStatus.objects.all().order_by('status_code')
        return [TournamentStatusMapper.to_domain(status) for status in django_statuses]

    def save_status(self, status: TournamentStatus) -> TournamentStatus:
        """保存或更新状态"""
        orm_data = TournamentStatusMapper.to_orm_data(status)

        django_status, created = DjangoTournamentStatus.objects.update_or_create(
            id=status.id,
            defaults=orm_data
        )

        return TournamentStatusMapper.to_domain(django_status)
