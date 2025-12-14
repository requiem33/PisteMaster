from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from django.db import IntegrityError

from core.models.pool_assignment import PoolAssignment
from backend.apps.fencing_organizer.repositories.pool_assignment_repo import DjangoPoolAssignmentRepository
from backend.apps.fencing_organizer.repositories.pool_repo import DjangoPoolRepository
from backend.apps.fencing_organizer.repositories.fencer_repo import DjangoFencerRepository
from backend.apps.fencing_organizer.repositories.event_participant_repo import DjangoEventParticipantRepository


class PoolAssignmentService:
    """PoolAssignment业务服务"""

    def __init__(self,
                 assignment_repository: Optional[DjangoPoolAssignmentRepository] = None,
                 pool_repository: Optional[DjangoPoolRepository] = None,
                 fencer_repository: Optional[DjangoFencerRepository] = None,
                 participant_repository: Optional[DjangoEventParticipantRepository] = None):

        self.assignment_repository = assignment_repository or DjangoPoolAssignmentRepository()
        self.pool_repository = pool_repository or DjangoPoolRepository()
        self.fencer_repository = fencer_repository or DjangoFencerRepository()
        self.participant_repository = participant_repository or DjangoEventParticipantRepository()

    def create_assignment(self, pool_id: UUID, fencer_id: UUID) -> PoolAssignment:
        """创建分配记录"""
        # 验证小组存在
        pool = self.pool_repository.get_pool_by_id(pool_id)
        if not pool:
            raise self.PoolAssignmentServiceError(f"小组 {pool_id} 不存在")

        # 验证运动员存在
        fencer = self.fencer_repository.get_fencer_by_id(fencer_id)
        if not fencer:
            raise self.PoolAssignmentServiceError(f"运动员 {fencer_id} 不存在")

        # 验证运动员是否参与了该事件
        participant = self.participant_repository.get_participant(pool.event_id, fencer_id)
        if not participant:
            raise self.PoolAssignmentServiceError(
                f"运动员 {fencer.display_name} 没有参加项目 {pool.event_id}"
            )

        # 创建分配记录
        try:
            assignment = self.assignment_repository.create_assignment(pool_id, fencer_id)
            return assignment
        except IntegrityError as e:
            if 'unique_pool_fencer' in str(e):
                # 已经分配，返回现有记录
                existing = self.assignment_repository.get_assignment(pool_id, fencer_id)
                if existing:
                    return existing
            raise self.PoolAssignmentServiceError(f"创建分配记录失败: {str(e)}")

    def get_assignments_by_pool(self, pool_id: UUID) -> List[PoolAssignment]:
        """获取小组分配记录"""
        return self.assignment_repository.get_assignments_by_pool(pool_id)

    def get_pool_ranking(self, pool_id: UUID) -> List[PoolAssignment]:
        """获取小组排名"""
        # 首先确保有计算过的排名
        assignments = self.assignment_repository.get_assignments_by_pool(pool_id)

        # 如果还没有排名，计算一次
        if not any(a.final_pool_rank for a in assignments):
            return self.assignment_repository.calculate_pool_ranking(pool_id)

        return assignments

    def update_match_result(self, pool_id: UUID, fencer_id: UUID,
                            touches_scored: int, touches_received: int, is_winner: bool) -> PoolAssignment:
        """更新比赛结果"""
        # 验证分配记录存在
        assignment = self.assignment_repository.get_assignment(pool_id, fencer_id)
        if not assignment:
            raise self.PoolAssignmentServiceError(f"运动员 {fencer_id} 不在小组 {pool_id} 中")

        # 验证比分有效性
        errors = {}
        if touches_scored < 0:
            errors['touches_scored'] = "得分不能为负数"
        if touches_received < 0:
            errors['touches_received'] = "失分不能为负数"

        # 获取目标分数（从小组的规则中）
        pool = self.pool_repository.get_pool_by_id(pool_id)
        if pool:
            # 这里需要获取小组对应的event和rule
            # 在实际实现中，需要查询数据库
            target_score = 5  # 默认5分
        else:
            target_score = 5

        if touches_scored > target_score:
            errors['touches_scored'] = f"得分不能超过目标分数 {target_score}"
        if touches_received > target_score:
            errors['touches_received'] = f"失分不能超过目标分数 {target_score}"

        if errors:
            raise self.PoolAssignmentServiceError("比分验证失败", errors)

        # 更新比赛结果
        updated_assignment = self.assignment_repository.update_match_result(
            pool_id, fencer_id, touches_scored, touches_received, is_winner
        )

        if not updated_assignment:
            raise self.PoolAssignmentServiceError("更新比赛结果失败")

        return updated_assignment

    def calculate_qualification_for_event(self, event_id: UUID, qualification_count: int) -> List[PoolAssignment]:
        """计算项目晋级排名"""
        # 验证事件存在
        from backend.apps.fencing_organizer.repositories.event_repo import DjangoEventRepository
        event_repository = DjangoEventRepository()
        event = event_repository.get_event_by_id(event_id)

        if not event:
            raise self.PoolAssignmentServiceError(f"项目 {event_id} 不存在")

        # 获取项目的晋级数量（从规则中）
        # 这里简化处理，使用传入的qualification_count
        # 实际应该从event.rule中获取

        return self.assignment_repository.calculate_qualification_ranking(event_id, qualification_count)

    def get_qualified_fencers_for_event(self, event_id: UUID) -> List[PoolAssignment]:
        """获取项目的晋级运动员"""
        return self.assignment_repository.get_qualified_fencers(event_id)

    def get_pool_assignment_details(self, pool_id: UUID) -> List[Dict[str, Any]]:
        """获取小组分配详情（包含运动员信息和统计）"""
        return self.assignment_repository.get_pool_assignments_with_fencers(pool_id)

    def reset_pool_assignments(self, pool_id: UUID) -> bool:
        """重置小组分配"""
        # 验证小组存在
        pool = self.pool_repository.get_pool_by_id(pool_id)
        if not pool:
            raise self.PoolAssignmentServiceError(f"小组 {pool_id} 不存在")

        return self.assignment_repository.reset_pool_assignments(pool_id)

    def assign_fencers_to_pool(self, pool_id: UUID, fencer_ids: List[UUID]) -> List[PoolAssignment]:
        """批量分配运动员到小组"""
        assignments = []

        for fencer_id in fencer_ids:
            try:
                assignment = self.create_assignment(pool_id, fencer_id)
                assignments.append(assignment)
            except self.PoolAssignmentServiceError as e:
                # 记录错误但继续分配其他运动员
                print(f"分配运动员 {fencer_id} 到小组 {pool_id} 失败: {e}")
                continue

        return assignments

    class PoolAssignmentServiceError(Exception):
        """Service层异常"""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
