from typing import Optional, List, Dict, Any
from uuid import UUID

from backend.apps.fencing_organizer.mappers.piste_mapper import PisteMapper
from backend.apps.fencing_organizer.modules.piste.models import DjangoPiste
from core.models.piste import Piste


class DjangoPisteRepository:
    """剑道仓库"""

    def get_by_id(self, piste_id: UUID) -> Optional[Piste]:
        """通过ID获取剑道"""
        try:
            django_piste = DjangoPiste.objects.select_related('tournament').get(pk=piste_id)
            return PisteMapper.to_domain(django_piste)
        except DjangoPiste.DoesNotExist:
            return None

    def get_by_tournament(self, tournament_id: UUID) -> List[Piste]:
        """获取指定赛事的剑道"""
        django_pistes = DjangoPiste.objects.select_related('tournament').filter(
            tournament_id=tournament_id
        ).order_by('piste_number')

        return [PisteMapper.to_domain(p) for p in django_pistes]

    def get_available_pistes(self, tournament_id: UUID) -> List[Piste]:
        """获取可用的剑道"""
        django_pistes = DjangoPiste.objects.select_related('tournament').filter(
            tournament_id=tournament_id,
            is_available=True
        ).order_by('piste_type', 'piste_number')

        return [PisteMapper.to_domain(p) for p in django_pistes]

    def get_main_pistes(self, tournament_id: UUID) -> List[Piste]:
        """获取主剑道"""
        django_pistes = DjangoPiste.objects.select_related('tournament').filter(
            tournament_id=tournament_id,
            piste_type='MAIN',
            is_available=True
        ).order_by('piste_number')

        return [PisteMapper.to_domain(p) for p in django_pistes]

    def save(self, piste: Piste) -> Piste:
        """保存剑道"""
        orm_data = PisteMapper.to_orm_data(piste)

        django_piste, created = DjangoPiste.objects.update_or_create(
            id=piste.id,
            defaults=orm_data
        )

        return PisteMapper.to_domain(django_piste)
