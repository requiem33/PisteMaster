from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from django.db.models import Q, Count, F
from django.db import transaction

from backend.apps.fencing_organizer.mappers.pool_mapper import PoolMapper
from backend.apps.fencing_organizer.modules.pool.models import DjangoPool
from core.interfaces.pool_repository import PoolRepositoryInterface
from core.models.pool import Pool
from core.constants.pool import PoolStatus


class DjangoPoolRepository(PoolRepositoryInterface):
    """小组仓库的Django实现"""

    def get_pool_by_id(self, pool_id: UUID) -> Optional[Pool]:
        """通过ID获取小组"""
        try:
            django_pool = DjangoPool.objects.select_related(
                'event', 'piste', 'event__tournament'
            ).get(pk=pool_id)
            return PoolMapper.to_domain(django_pool)
        except DjangoPool.DoesNotExist:
            return None

    def get_pools_by_event(self, event_id: UUID) -> List[Pool]:
        """获取指定项目的小组"""
        django_pools = DjangoPool.objects.select_related(
            'event', 'piste', 'event__tournament'
        ).filter(
            event_id=event_id
        ).order_by('pool_number')

        return [PoolMapper.to_domain(p) for p in django_pools]

    def get_pools_by_event_and_status(self, event_id: UUID, status: str) -> List[Pool]:
        """获取指定项目和状态的小组"""
        django_pools = DjangoPool.objects.select_related(
            'event', 'piste', 'event__tournament'
        ).filter(
            event_id=event_id,
            status=status
        ).order_by('pool_number')

        return [PoolMapper.to_domain(p) for p in django_pools]

    def get_pools_by_piste(self, piste_id: UUID) -> List[Pool]:
        """获取指定剑道的小组"""
        django_pools = DjangoPool.objects.select_related(
            'event', 'piste', 'event__tournament'
        ).filter(
            piste_id=piste_id
        ).order_by('start_time')

        return [PoolMapper.to_domain(p) for p in django_pools]

    def get_pools_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Pool]:
        """获取指定时间范围内的小组"""
        django_pools = DjangoPool.objects.select_related(
            'event', 'piste', 'event__tournament'
        ).filter(
            Q(start_time__gte=start_date) & Q(start_time__lte=end_date)
        ).order_by('start_time')

        return [PoolMapper.to_domain(p) for p in django_pools]

    def get_all_pools(self) -> List[Pool]:
        """获取所有小组"""
        django_pools = DjangoPool.objects.select_related(
            'event', 'piste', 'event__tournament'
        ).all().order_by('-start_time')

        return [PoolMapper.to_domain(p) for p in django_pools]

    def save_pool(self, pool: Pool) -> Pool:
        """保存或更新小组"""
        orm_data = PoolMapper.to_orm_data(pool)

        django_pool, created = DjangoPool.objects.update_or_create(
            id=pool.id,
            defaults=orm_data
        )

        return PoolMapper.to_domain(django_pool)

    def delete_pool(self, pool_id: UUID) -> bool:
        """删除小组"""
        try:
            count, _ = DjangoPool.objects.filter(id=pool_id).delete()
            return count > 0
        except Exception:
            return False

    def get_next_pool_number(self, event_id: UUID) -> int:
        """获取下一个可用的小组编号"""
        last_pool = DjangoPool.objects.filter(
            event_id=event_id
        ).order_by('-pool_number').first()

        if last_pool:
            return last_pool.pool_number + 1
        return 1

    def get_active_pools(self) -> List[Pool]:
        """获取活跃的小组（非已完成/已取消）"""
        django_pools = DjangoPool.objects.select_related(
            'event', 'piste', 'event__tournament'
        ).exclude(
            status__in=[PoolStatus.COMPLETED.value, PoolStatus.CANCELLED.value]
        ).order_by('start_time')

        return [PoolMapper.to_domain(p) for p in django_pools]

    def get_pools_with_stats(self, event_id: UUID) -> List[Dict[str, Any]]:
        """获取小组及统计信息"""
        pools = DjangoPool.objects.filter(
            event_id=event_id
        ).annotate(
            participant_count=Count('participants'),
            bout_count=Count('bouts'),
            completed_bout_count=Count('bouts', filter=Q(bouts__status__status_code='COMPLETED'))
        ).select_related('event', 'piste').order_by('pool_number')

        result = []
        for pool in pools:
            pool_data = PoolMapper.to_domain(pool)
            result.append({
                "pool": pool_data,
                "stats": {
                    "participant_count": pool.participant_count,
                    "bout_count": pool.bout_count,
                    "completed_bout_count": pool.completed_bout_count,
                    "completion_percentage": (
                            pool.completed_bout_count / pool.bout_count * 100) if pool.bout_count > 0 else 0
                }
            })

        return result

    def assign_piste_to_pools(self, pool_ids: List[UUID], piste_id: UUID) -> List[Pool]:
        """为多个小组分配剑道"""
        with transaction.atomic():
            updated_pools = []
            for pool_id in pool_ids:
                try:
                    pool = DjangoPool.objects.get(id=pool_id)
                    pool.piste_id = piste_id
                    pool.save()
                    updated_pools.append(PoolMapper.to_domain(pool))
                except DjangoPool.DoesNotExist:
                    continue

            return updated_pools

    def update_pool_status(self, pool_id: UUID, status: str) -> Optional[Pool]:
        """更新小组状态"""
        try:
            pool = DjangoPool.objects.get(id=pool_id)
            pool.status = status
            pool.save()
            return PoolMapper.to_domain(pool)
        except DjangoPool.DoesNotExist:
            return None
