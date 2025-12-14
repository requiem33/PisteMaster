from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from django.db.models import Q, Count, Sum, Avg
from django.db import transaction
import operator

from backend.apps.fencing_organizer.mappers.pool_assignment_mapper import PoolAssignmentMapper
from backend.apps.fencing_organizer.modules.pool_assignment.models import DjangoPoolAssignment
from core.interfaces.pool_assignment_repository import PoolAssignmentRepositoryInterface
from core.models.pool_assignment import PoolAssignment


class DjangoPoolAssignmentRepository(PoolAssignmentRepositoryInterface):
    """PoolAssignment仓库的Django实现"""

    def get_assignment_by_id(self, assignment_id: UUID) -> Optional[PoolAssignment]:
        """根据ID获取分配记录"""
        try:
            django_assignment = DjangoPoolAssignment.objects.select_related(
                'pool', 'fencer'
            ).get(pk=assignment_id)
            return PoolAssignmentMapper.to_domain(django_assignment)
        except DjangoPoolAssignment.DoesNotExist:
            return None

    def get_assignments_by_pool(self, pool_id: UUID) -> List[PoolAssignment]:
        """获取指定小组的所有分配记录"""
        assignments = DjangoPoolAssignment.objects.filter(
            pool_id=pool_id
        ).select_related('pool', 'fencer').order_by('final_pool_rank')

        return [PoolAssignmentMapper.to_domain(a) for a in assignments]

    def get_assignments_by_fencer(self, fencer_id: UUID) -> List[PoolAssignment]:
        """获取指定运动员的所有小组分配记录"""
        assignments = DjangoPoolAssignment.objects.filter(
            fencer_id=fencer_id
        ).select_related('pool', 'fencer').order_by('-pool__event__start_time')

        return [PoolAssignmentMapper.to_domain(a) for a in assignments]

    def get_assignment(self, pool_id: UUID, fencer_id: UUID) -> Optional[PoolAssignment]:
        """获取指定小组和运动员的分配记录"""
        try:
            django_assignment = DjangoPoolAssignment.objects.select_related(
                'pool', 'fencer'
            ).get(pool_id=pool_id, fencer_id=fencer_id)
            return PoolAssignmentMapper.to_domain(django_assignment)
        except DjangoPoolAssignment.DoesNotExist:
            return None

    def save_assignment(self, assignment: PoolAssignment) -> PoolAssignment:
        """保存或更新分配记录"""
        orm_data = PoolAssignmentMapper.to_orm_data(assignment)

        django_assignment, created = DjangoPoolAssignment.objects.update_or_create(
            id=assignment.id,
            defaults=orm_data
        )

        return PoolAssignmentMapper.to_domain(django_assignment)

    def delete_assignment(self, pool_id: UUID, fencer_id: UUID) -> bool:
        """删除分配记录"""
        try:
            count, _ = DjangoPoolAssignment.objects.filter(
                pool_id=pool_id,
                fencer_id=fencer_id
            ).delete()
            return count > 0
        except Exception:
            return False

    def create_assignment(self, pool_id: UUID, fencer_id: UUID) -> PoolAssignment:
        """创建分配记录"""
        # 检查是否已存在
        existing = self.get_assignment(pool_id, fencer_id)
        if existing:
            return existing

        # 创建新的分配记录
        assignment = PoolAssignment(
            pool_id=pool_id,
            fencer_id=fencer_id,
            victories=0,
            indicator=0,
            touches_scored=0,
            touches_received=0,
            matches_played=0,
            is_qualified=False
        )

        return self.save_assignment(assignment)

    def update_ranking(self, pool_id: UUID, ranking_updates: List[Dict[str, Any]]) -> List[PoolAssignment]:
        """更新排名"""
        updated_assignments = []

        with transaction.atomic():
            for update in ranking_updates:
                fencer_id = update.get('fencer_id')
                final_pool_rank = update.get('final_pool_rank')
                is_qualified = update.get('is_qualified', False)
                qualification_rank = update.get('qualification_rank')

                if not fencer_id or not final_pool_rank:
                    continue

                try:
                    assignment = DjangoPoolAssignment.objects.get(
                        pool_id=pool_id,
                        fencer_id=fencer_id
                    )
                    assignment.final_pool_rank = final_pool_rank
                    assignment.is_qualified = is_qualified
                    assignment.qualification_rank = qualification_rank
                    assignment.save()

                    updated_assignments.append(PoolAssignmentMapper.to_domain(assignment))
                except DjangoPoolAssignment.DoesNotExist:
                    continue

        return updated_assignments

    def calculate_pool_ranking(self, pool_id: UUID) -> List[PoolAssignment]:
        """计算小组排名（根据击剑规则）"""
        assignments = self.get_assignments_by_pool(pool_id)

        if not assignments:
            return []

        # 第一步：按胜场数排序
        sorted_assignments = sorted(
            assignments,
            key=lambda x: (x.victories, x.indicator, x.touches_scored),
            reverse=True
        )

        # 处理平局：如果有完全相同的胜场数、得失分差和总得分，需要检查直接对战结果
        # 这里简化处理，直接按已有排序
        for i, assignment in enumerate(sorted_assignments, 1):
            assignment.final_pool_rank = i

        # 保存排名
        with transaction.atomic():
            for assignment in sorted_assignments:
                self.save_assignment(assignment)

        return sorted_assignments

    def get_pool_stats(self, pool_id: UUID) -> Dict[str, Any]:
        """获取小组统计"""
        stats = DjangoPoolAssignment.objects.filter(pool_id=pool_id).aggregate(
            total_assignments=Count('id'),
            total_matches_played=Sum('matches_played'),
            total_victories=Sum('victories'),
            total_touches_scored=Sum('touches_scored'),
            total_touches_received=Sum('touches_received'),
            average_win_rate=Avg('victories') / Avg('matches_played') * 100
        )

        # 获取排名分布
        ranked_count = DjangoPoolAssignment.objects.filter(
            pool_id=pool_id,
            final_pool_rank__isnull=False
        ).count()

        qualified_count = DjangoPoolAssignment.objects.filter(
            pool_id=pool_id,
            is_qualified=True
        ).count()

        stats['ranked_count'] = ranked_count
        stats['qualified_count'] = qualified_count

        return stats

    def update_match_result(self, pool_id: UUID, fencer_id: UUID,
                            touches_scored: int, touches_received: int, is_winner: bool) -> Optional[PoolAssignment]:
        """更新比赛结果"""
        try:
            assignment = DjangoPoolAssignment.objects.get(
                pool_id=pool_id,
                fencer_id=fencer_id
            )

            assignment.matches_played += 1
            assignment.touches_scored += touches_scored
            assignment.touches_received += touches_received

            if is_winner:
                assignment.victories += 1

            assignment.save()

            # 重新计算排名
            self.calculate_pool_ranking(pool_id)

            return PoolAssignmentMapper.to_domain(assignment)
        except DjangoPoolAssignment.DoesNotExist:
            return None

    def get_qualified_fencers(self, event_id: UUID) -> List[PoolAssignment]:
        """获取晋级的运动员"""
        from backend.apps.fencing_organizer.modules.pool.models import DjangoPool

        # 获取该事件的所有小组
        pool_ids = DjangoPool.objects.filter(event_id=event_id).values_list('id', flat=True)

        assignments = DjangoPoolAssignment.objects.filter(
            pool_id__in=pool_ids,
            is_qualified=True
        ).select_related('pool', 'fencer').order_by('qualification_rank')

        return [PoolAssignmentMapper.to_domain(a) for a in assignments]

    def calculate_qualification_ranking(self, event_id: UUID, qualification_count: int) -> List[PoolAssignment]:
        """计算晋级排名"""
        from backend.apps.fencing_organizer.modules.pool.models import DjangoPool

        # 获取该事件的所有小组
        pool_ids = DjangoPool.objects.filter(event_id=event_id).values_list('id', flat=True)

        # 获取所有小组中排名靠前的运动员
        all_assignments = []
        for pool_id in pool_ids:
            assignments = self.get_assignments_by_pool(pool_id)
            all_assignments.extend(assignments)

        # 按小组排名和胜负记录排序
        sorted_assignments = sorted(
            all_assignments,
            key=lambda x: (
                x.is_qualified,  # 优先已经标记为晋级的
                x.final_pool_rank if x.final_pool_rank else float('inf'),  # 小组排名靠前的优先
                x.victories,  # 胜场数多的优先
                x.indicator,  # 得失分差大的优先
                x.touches_scored  # 总得分多的优先
            )
        )

        # 标记晋级者
        for i, assignment in enumerate(sorted_assignments[:qualification_count], 1):
            assignment.is_qualified = True
            assignment.qualification_rank = i
            self.save_assignment(assignment)

        # 标记未晋级者
        for assignment in sorted_assignments[qualification_count:]:
            assignment.is_qualified = False
            assignment.qualification_rank = None
            self.save_assignment(assignment)

        return sorted_assignments[:qualification_count]

    def reset_pool_assignments(self, pool_id: UUID) -> bool:
        """重置小组分配（清除所有排名和统计）"""
        try:
            DjangoPoolAssignment.objects.filter(pool_id=pool_id).update(
                final_pool_rank=None,
                victories=0,
                indicator=0,
                touches_scored=0,
                touches_received=0,
                matches_played=0,
                is_qualified=False,
                qualification_rank=None
            )
            return True
        except Exception:
            return False

    def get_pool_assignments_with_fencers(self, pool_id: UUID) -> List[Dict[str, Any]]:
        """获取小组分配记录（包含运动员信息）"""
        assignments = DjangoPoolAssignment.objects.filter(
            pool_id=pool_id
        ).select_related('fencer', 'pool').order_by('final_pool_rank')

        result = []
        for assignment in assignments:
            result.append({
                'assignment': PoolAssignmentMapper.to_domain(assignment),
                'fencer': {
                    'id': assignment.fencer.id,
                    'display_name': assignment.fencer.display_name,
                    'country_code': assignment.fencer.country_code,
                    'current_ranking': assignment.fencer.current_ranking,
                    'primary_weapon': assignment.fencer.primary_weapon
                },
                'stats': {
                    'win_rate': assignment.win_rate,
                    'average_touches_scored': assignment.average_touches_scored,
                    'average_touches_received': assignment.average_touches_received
                }
            })

        return result
