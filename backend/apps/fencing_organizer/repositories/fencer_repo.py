from typing import Optional, List, Dict, Any
from uuid import UUID
from django.db.models import Q
from django.core.exceptions import MultipleObjectsReturned
import re

from backend.apps.fencing_organizer.mappers.fencer_mapper import FencerMapper
from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
from core.interfaces.fencer_repository import FencerRepositoryInterface
from core.models.fencer import Fencer


class DjangoFencerRepository(FencerRepositoryInterface):
    """Fencer仓库的Django实现"""

    def get_fencer_by_id(self, fencer_id: UUID) -> Optional[Fencer]:
        """根据ID获取运动员"""
        try:
            django_fencer = DjangoFencer.objects.get(pk=fencer_id)
            return FencerMapper.to_domain(django_fencer)
        except DjangoFencer.DoesNotExist:
            return None

    def get_fencer_by_fencing_id(self, fencing_id: str) -> Optional[Fencer]:
        """根据击剑ID获取运动员"""
        try:
            django_fencer = DjangoFencer.objects.get(fencing_id=fencing_id)
            return FencerMapper.to_domain(django_fencer)
        except DjangoFencer.DoesNotExist:
            return None
        except MultipleObjectsReturned:
            # 理论上不应该发生，因为fencing_id是unique的
            django_fencers = DjangoFencer.objects.filter(fencing_id=fencing_id)
            if django_fencers.exists():
                return FencerMapper.to_domain(django_fencers.first())
            return None

    def get_fencers_by_country(self, country_code: str) -> List[Fencer]:
        """根据国家获取运动员列表"""
        django_fencers = DjangoFencer.objects.filter(
            country_code=country_code.upper()
        ).order_by('last_name', 'first_name')

        return [FencerMapper.to_domain(fencer) for fencer in django_fencers]

    def get_fencers_by_name(self, first_name: Optional[str] = None,
                            last_name: Optional[str] = None) -> List[Fencer]:
        """根据姓名获取运动员列表"""
        query = Q()

        if first_name:
            query &= Q(first_name__icontains=first_name)

        if last_name:
            query &= Q(last_name__icontains=last_name)

        django_fencers = DjangoFencer.objects.filter(query).order_by('last_name', 'first_name')
        return [FencerMapper.to_domain(fencer) for fencer in django_fencers]

    def get_all_fencers(self, skip: int = 0, limit: int = 100) -> List[Fencer]:
        """获取所有运动员"""
        django_fencers = DjangoFencer.objects.all().order_by('last_name', 'first_name')

        # 应用分页
        if skip:
            django_fencers = django_fencers[skip:]
        if limit:
            django_fencers = django_fencers[:limit]

        return [FencerMapper.to_domain(fencer) for fencer in django_fencers]

    def save_fencer(self, fencer: Fencer) -> Fencer:
        """保存或更新运动员"""
        orm_data = FencerMapper.to_orm_data(fencer)

        django_fencer, created = DjangoFencer.objects.update_or_create(
            id=fencer.id,
            defaults=orm_data
        )

        return FencerMapper.to_domain(django_fencer)

    def delete_fencer(self, fencer_id: UUID) -> bool:
        """删除运动员"""
        try:
            count, _ = DjangoFencer.objects.filter(id=fencer_id).delete()
            return count > 0
        except Exception:
            return False

    def search_fencers(self, query: str, limit: int = 50) -> List[Fencer]:
        """搜索运动员"""
        # 分割查询词
        search_terms = query.strip().split()

        # 构建查询
        q_objects = Q()

        for term in search_terms:
            if len(term) < 2:  # 忽略太短的词
                continue

            q_objects |= Q(first_name__icontains=term)
            q_objects |= Q(last_name__icontains=term)
            q_objects |= Q(display_name__icontains=term)
            q_objects |= Q(fencing_id__icontains=term)
            q_objects |= Q(country_code__icontains=term.upper())

        # 如果没有有效的查询词，返回空列表
        if not q_objects:
            return []

        django_fencers = DjangoFencer.objects.filter(q_objects).order_by('last_name', 'first_name')[:limit]
        return [FencerMapper.to_domain(fencer) for fencer in django_fencers]

    def get_fencers_by_weapon(self, weapon: str) -> List[Fencer]:
        """根据主剑种获取运动员"""
        django_fencers = DjangoFencer.objects.filter(
            primary_weapon=weapon.upper()
        ).order_by('current_ranking', 'last_name', 'first_name')

        return [FencerMapper.to_domain(fencer) for fencer in django_fencers]

    def get_top_ranked_fencers(self, limit: int = 100, country: Optional[str] = None) -> List[Fencer]:
        """获取排名最高的运动员"""
        query = DjangoFencer.objects.filter(current_ranking__isnull=False)

        if country:
            query = query.filter(country_code=country.upper())

        django_fencers = query.order_by('current_ranking')[:limit]
        return [FencerMapper.to_domain(fencer) for fencer in django_fencers]

    def count_fencers(self) -> Dict[str, int]:
        """统计运动员数量"""
        stats = {
            'total': DjangoFencer.objects.count(),
            'with_fencing_id': DjangoFencer.objects.exclude(fencing_id__isnull=True).count(),
            'by_gender': {},
            'by_weapon': {}
        }

        # 按性别统计
        genders = DjangoFencer.objects.values('gender').annotate(count=models.Count('gender'))
        for gender in genders:
            if gender['gender']:
                stats['by_gender'][gender['gender']] = gender['count']

        # 按剑种统计
        weapons = DjangoFencer.objects.values('primary_weapon').annotate(count=models.Count('primary_weapon'))
        for weapon in weapons:
            if weapon['primary_weapon']:
                stats['by_weapon'][weapon['primary_weapon']] = weapon['count']

        return stats
