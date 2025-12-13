from typing import Optional, List
from uuid import UUID
from datetime import date
from django.db.models import Q

from backend.apps.fencing_organizer.mappers.tournament_mapper import TournamentMapper
from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament
from core.interfaces.tournament_repository import TournamentRepositoryInterface
from core.models.tournament import Tournament


class DjangoTournamentRepository(TournamentRepositoryInterface):
    """赛事仓库的Django实现"""

    def get_tournament_by_id(self, tournament_id: UUID) -> Optional[Tournament]:
        """通过ID获取赛事"""
        try:
            django_tournament = DjangoTournament.objects.select_related('status').get(pk=tournament_id)
            return TournamentMapper.to_domain(django_tournament)
        except DjangoTournament.DoesNotExist:
            return None

    def get_tournaments_by_date_range(self, start_date: date, end_date: date) -> List[Tournament]:
        """获取指定日期范围内的赛事"""
        # 查找与给定日期范围有重叠的赛事
        django_tournaments = DjangoTournament.objects.select_related('status').filter(
            Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
        ).order_by('start_date')

        return [TournamentMapper.to_domain(t) for t in django_tournaments]

    def get_tournaments_by_status(self, status_id: UUID) -> List[Tournament]:
        """获取指定状态的赛事"""
        django_tournaments = DjangoTournament.objects.select_related('status').filter(
            status_id=status_id
        ).order_by('-start_date')

        return [TournamentMapper.to_domain(t) for t in django_tournaments]

    def get_all_tournaments(self) -> List[Tournament]:
        """获取所有赛事"""
        django_tournaments = DjangoTournament.objects.select_related('status').all().order_by('-start_date')
        return [TournamentMapper.to_domain(t) for t in django_tournaments]

    def save_tournament(self, tournament: Tournament) -> Tournament:
        """保存或更新赛事"""
        orm_data = TournamentMapper.to_orm_data(tournament)

        django_tournament, created = DjangoTournament.objects.update_or_create(
            id=tournament.id,
            defaults=orm_data
        )

        return TournamentMapper.to_domain(django_tournament)

    def delete_tournament(self, tournament_id: UUID) -> bool:
        """删除赛事"""
        try:
            count, _ = DjangoTournament.objects.filter(id=tournament_id).delete()
            return count > 0
        except Exception:
            return False

    def search_tournaments(self, **filters) -> List[Tournament]:
        """搜索赛事"""
        queryset = DjangoTournament.objects.select_related('status')

        # 应用过滤器
        if 'name' in filters:
            queryset = queryset.filter(tournament_name__icontains=filters['name'])
        if 'organizer' in filters:
            queryset = queryset.filter(organizer__icontains=filters['organizer'])
        if 'location' in filters:
            queryset = queryset.filter(location__icontains=filters['location'])
        if 'status_code' in filters:
            queryset = queryset.filter(status__status_code=filters['status_code'])
        if 'date_range' in filters:
            start_date, end_date = filters['date_range']
            queryset = queryset.filter(
                Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
            )

        # 排序
        ordering = filters.get('ordering', '-start_date')
        if ordering:
            queryset = queryset.order_by(ordering)

        return [TournamentMapper.to_domain(t) for t in queryset]
