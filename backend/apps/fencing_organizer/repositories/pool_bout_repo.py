from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from django.db.models import Q, Count
from django.db import transaction

from backend.apps.fencing_organizer.mappers.pool_bout_mapper import PoolBoutMapper
from backend.apps.fencing_organizer.modules.pool_bout.models import DjangoPoolBout
from core.interfaces.pool_bout_repository import PoolBoutRepositoryInterface
from core.models.pool_bout import PoolBout


class DjangoPoolBoutRepository(PoolBoutRepositoryInterface):
    """小组赛单场比赛仓库的Django实现"""

    def get_bout_by_id(self, bout_id: UUID) -> Optional[PoolBout]:
        """通过ID获取比赛"""
        try:
            django_bout = DjangoPoolBout.objects.select_related(
                'pool', 'fencer_a', 'fencer_b', 'winner', 'status'
            ).get(pk=bout_id)
            return PoolBoutMapper.to_domain(django_bout)
        except DjangoPoolBout.DoesNotExist:
            return None

    def get_bouts_by_pool(self, pool_id: UUID) -> List[PoolBout]:
        """获取指定小组的所有比赛"""
        django_bouts = DjangoPoolBout.objects.select_related(
            'pool', 'fencer_a', 'fencer_b', 'winner', 'status'
        ).filter(
            pool_id=pool_id
        ).order_by('scheduled_time')

        return [PoolBoutMapper.to_domain(b) for b in django_bouts]

    def get_bouts_by_fencer(self, fencer_id: UUID) -> List[PoolBout]:
        """获取指定运动员的所有比赛"""
        django_bouts = DjangoPoolBout.objects.select_related(
            'pool', 'fencer_a', 'fencer_b', 'winner', 'status'
        ).filter(
            Q(fencer_a_id=fencer_id) | Q(fencer_b_id=fencer_id)
        ).order_by('-scheduled_time')

        return [PoolBoutMapper.to_domain(b) for b in django_bouts]

    def get_bouts_by_status(self, status_id: UUID) -> List[PoolBout]:
        """获取指定状态的所有比赛"""
        django_bouts = DjangoPoolBout.objects.select_related(
            'pool', 'fencer_a', 'fencer_b', 'winner', 'status'
        ).filter(
            status_id=status_id
        ).order_by('scheduled_time')

        return [PoolBoutMapper.to_domain(b) for b in django_bouts]

    def get_bouts_by_date_range(self, start_date: datetime, end_date: datetime) -> List[PoolBout]:
        """获取指定时间范围内的比赛"""
        django_bouts = DjangoPoolBout.objects.select_related(
            'pool', 'fencer_a', 'fencer_b', 'winner', 'status'
        ).filter(
            Q(scheduled_time__gte=start_date) & Q(scheduled_time__lte=end_date)
        ).order_by('scheduled_time')

        return [PoolBoutMapper.to_domain(b) for b in django_bouts]

    def get_all_bouts(self) -> List[PoolBout]:
        """获取所有比赛"""
        django_bouts = DjangoPoolBout.objects.select_related(
            'pool', 'fencer_a', 'fencer_b', 'winner', 'status'
        ).all().order_by('-scheduled_time')

        return [PoolBoutMapper.to_domain(b) for b in django_bouts]

    def save_bout(self, bout: PoolBout) -> PoolBout:
        """保存或更新比赛"""
        orm_data = PoolBoutMapper.to_orm_data(bout)

        django_bout, created = DjangoPoolBout.objects.update_or_create(
            id=bout.id,
            defaults=orm_data
        )

        return PoolBoutMapper.to_domain(django_bout)

    def delete_bout(self, bout_id: UUID) -> bool:
        """删除比赛"""
        try:
            count, _ = DjangoPoolBout.objects.filter(id=bout_id).delete()
            return count > 0
        except Exception:
            return False

    def get_bout_by_fencers(self, pool_id: UUID, fencer_a_id: UUID, fencer_b_id: UUID) -> Optional[PoolBout]:
        """获取指定运动员对之间的比赛"""
        # 确保fencer_a_id < fencer_b_id
        fencer_a = min(fencer_a_id, fencer_b_id)
        fencer_b = max(fencer_a_id, fencer_b_id)

        try:
            django_bout = DjangoPoolBout.objects.select_related(
                'pool', 'fencer_a', 'fencer_b', 'winner', 'status'
            ).get(
                pool_id=pool_id,
                fencer_a_id=fencer_a,
                fencer_b_id=fencer_b
            )
            return PoolBoutMapper.to_domain(django_bout)
        except DjangoPoolBout.DoesNotExist:
            return None

    def get_upcoming_bouts(self, hours: int = 24) -> List[PoolBout]:
        """获取即将到来的比赛（未来N小时内）"""
        now = datetime.now()
        future_time = now + datetime.timedelta(hours=hours)

        django_bouts = DjangoPoolBout.objects.select_related(
            'pool', 'fencer_a', 'fencer_b', 'winner', 'status'
        ).filter(
            Q(scheduled_time__gte=now) & Q(scheduled_time__lte=future_time),
            status__status_code__in=['SCHEDULED', 'READY']
        ).order_by('scheduled_time')

        return [PoolBoutMapper.to_domain(b) for b in django_bouts]

    def get_active_bouts(self) -> List[PoolBout]:
        """获取活跃的比赛（非已完成/已取消）"""
        django_bouts = DjangoPoolBout.objects.select_related(
            'pool', 'fencer_a', 'fencer_b', 'winner', 'status'
        ).exclude(
            status__status_code__in=['COMPLETED', 'CANCELLED']
        ).order_by('scheduled_time')

        return [PoolBoutMapper.to_domain(b) for b in django_bouts]

    def generate_round_robin_bouts(self, pool_id: UUID) -> List[PoolBout]:
        """为小组生成循环赛对阵"""
        from backend.apps.fencing_organizer.modules.pool.models import DjangoPool
        from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer

        try:
            pool = DjangoPool.objects.get(id=pool_id)
            # 获取小组成员（这里假设小组成员关系已建立）
            # 在实际实现中，需要根据PoolAssignment获取小组成员
            # 这里暂时返回空列表，实际使用时需要实现

            # 示例：假设我们已经有fencer_ids列表
            # fencer_ids = [...]
            # 然后生成所有可能的对阵组合

            return []
        except DjangoPool.DoesNotExist:
            return []

    def update_bout_result(self, bout_id: UUID, fencer_a_score: int, fencer_b_score: int,
                           winner_id: Optional[UUID] = None) -> Optional[PoolBout]:
        """更新比赛结果"""
        try:
            bout = DjangoPoolBout.objects.get(id=bout_id)
            bout.fencer_a_score = fencer_a_score
            bout.fencer_b_score = fencer_b_score
            bout.winner_id = winner_id

            # 自动设置状态为已完成
            from backend.apps.fencing_organizer.modules.match_status.models import DjangoMatchStatusType
            completed_status = DjangoMatchStatusType.objects.get(status_code='COMPLETED')
            bout.status = completed_status

            bout.save()
            return PoolBoutMapper.to_domain(bout)
        except DjangoPoolBout.DoesNotExist:
            return None

    def get_bout_stats(self, pool_id: UUID) -> Dict[str, Any]:
        """获取小组比赛统计"""
        stats = DjangoPoolBout.objects.filter(pool_id=pool_id).aggregate(
            total_bouts=Count('id'),
            completed_bouts=Count('id', filter=Q(status__status_code='COMPLETED')),
            scheduled_bouts=Count('id', filter=Q(status__status_code='SCHEDULED')),
            in_progress_bouts=Count('id', filter=Q(status__status_code='IN_PROGRESS')),
        )

        return stats
