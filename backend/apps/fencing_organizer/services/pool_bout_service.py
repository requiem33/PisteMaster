from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from itertools import combinations
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError

from core.models.pool_bout import PoolBout
from core.constants.match_status import MatchStatusCode
from backend.apps.fencing_organizer.repositories.pool_bout_repo import DjangoPoolBoutRepository
from backend.apps.fencing_organizer.repositories.pool_repo import DjangoPoolRepository
from backend.apps.fencing_organizer.repositories.fencer_repo import DjangoFencerRepository
from backend.apps.fencing_organizer.repositories.match_status_repo import DjangoMatchStatusRepository


class PoolBoutService:
    """小组赛单场比赛业务服务"""

    def __init__(self,
                 bout_repository: Optional[DjangoPoolBoutRepository] = None,
                 pool_repository: Optional[DjangoPoolRepository] = None,
                 fencer_repository: Optional[DjangoFencerRepository] = None,
                 match_status_repository: Optional[DjangoMatchStatusRepository] = None):

        self.bout_repository = bout_repository or DjangoPoolBoutRepository()
        self.pool_repository = pool_repository or DjangoPoolRepository()
        self.fencer_repository = fencer_repository or DjangoFencerRepository()
        self.match_status_repository = match_status_repository or DjangoMatchStatusRepository()

    def get_bout_by_id(self, bout_id: UUID) -> Optional[PoolBout]:
        """根据ID获取比赛"""
        return self.bout_repository.get_bout_by_id(bout_id)

    def get_bouts_by_pool(self, pool_id: UUID) -> List[PoolBout]:
        """根据小组获取比赛"""
        return self.bout_repository.get_bouts_by_pool(pool_id)

    def get_upcoming_bouts(self, hours: int = 24) -> List[PoolBout]:
        """获取即将到来的比赛"""
        return self.bout_repository.get_upcoming_bouts(hours)

    def get_active_bouts(self) -> List[PoolBout]:
        """获取活跃的比赛"""
        return self.bout_repository.get_active_bouts()

    def create_bout(self, bout_data: dict) -> PoolBout:
        """创建比赛"""
        # 验证数据
        self._validate_bout_data(bout_data, is_create=True)

        # 验证外键存在性
        self._validate_foreign_keys(bout_data)

        # 创建Domain对象
        bout = PoolBout(**bout_data)

        # 通过Repository保存
        try:
            return self.bout_repository.save_bout(bout)
        except IntegrityError as e:
            if 'unique_pool_bout_pair' in str(e):
                raise self.PoolBoutServiceError("这两名运动员在该小组中已有比赛安排")
            raise self.PoolBoutServiceError(f"创建比赛失败: {str(e)}")

    def generate_round_robin_bouts(self, pool_id: UUID) -> List[PoolBout]:
        """为小组生成循环赛对阵"""
        # 获取小组信息
        pool = self.pool_repository.get_pool_by_id(pool_id)
        if not pool:
            raise self.PoolBoutServiceError(f"小组 {pool_id} 不存在")

        # 获取小组成员（这里需要从PoolAssignment获取，暂时模拟）
        # 在实际实现中，需要调用PoolAssignment服务
        fencer_ids = self._get_pool_fencers(pool_id)

        if len(fencer_ids) < 2:
            raise self.PoolBoutServiceError("小组成员不足，无法生成对阵")

        # 生成所有可能的对阵组合
        bout_pairs = list(combinations(fencer_ids, 2))

        # 获取默认状态
        scheduled_status = self.match_status_repository.get_by_code('SCHEDULED')
        if not scheduled_status:
            raise self.PoolBoutServiceError("找不到 'SCHEDULED' 比赛状态")

        created_bouts = []

        for fencer_a_id, fencer_b_id in bout_pairs:
            # 检查是否已存在
            existing_bout = self.bout_repository.get_bout_by_fencers(pool_id, fencer_a_id, fencer_b_id)
            if existing_bout:
                continue

            bout_data = {
                'pool_id': pool_id,
                'fencer_a_id': fencer_a_id,
                'fencer_b_id': fencer_b_id,
                'status_id': scheduled_status.id,
                'scheduled_time': pool.start_time  # 使用小组开始时间
            }

            try:
                bout = self.create_bout(bout_data)
                created_bouts.append(bout)
            except self.PoolBoutServiceError:
                continue

        return created_bouts

    def update_bout(self, bout_id: UUID, bout_data: dict) -> PoolBout:
        """更新比赛"""
        # 检查比赛是否存在
        existing_bout = self.bout_repository.get_bout_by_id(bout_id)
        if not existing_bout:
            raise self.PoolBoutServiceError(f"比赛 {bout_id} 不存在")

        # 验证数据
        self._validate_bout_data(bout_data, is_create=False)

        # 验证状态转移
        if 'status_id' in bout_data:
            new_status = self.match_status_repository.get_by_id(bout_data['status_id'])
            if new_status:
                self._validate_status_transition(existing_bout.status_id, bout_data['status_id'])

        # 验证外键存在性
        self._validate_foreign_keys(bout_data)

        # 更新属性
        for key, value in bout_data.items():
            if hasattr(existing_bout, key):
                setattr(existing_bout, key, value)

        # 通过Repository保存
        try:
            return self.bout_repository.save_bout(existing_bout)
        except IntegrityError as e:
            if 'unique_pool_bout_pair' in str(e):
                raise self.PoolBoutServiceError("这两名运动员在该小组中已有比赛安排")
            raise self.PoolBoutServiceError(f"更新比赛失败: {str(e)}")

    def update_bout_result(self, bout_id: UUID, fencer_a_score: int, fencer_b_score: int,
                           winner_id: Optional[UUID] = None) -> PoolBout:
        """更新比赛结果"""
        # 检查比赛是否存在
        bout = self.bout_repository.get_bout_by_id(bout_id)
        if not bout:
            raise self.PoolBoutServiceError(f"比赛 {bout_id} 不存在")

        # 验证比分
        self._validate_scores(fencer_a_score, fencer_b_score, bout)

        # 验证胜者
        if winner_id:
            self._validate_winner(winner_id, bout.fencer_a_id, bout.fencer_b_id)
        else:
            # 如果没有指定胜者，根据比分自动判断
            if fencer_a_score > fencer_b_score:
                winner_id = bout.fencer_a_id
            elif fencer_b_score > fencer_a_score:
                winner_id = bout.fencer_b_id
            # 平局时winner_id为None

        # 获取完成状态
        completed_status = self.match_status_repository.get_by_code('COMPLETED')
        if not completed_status:
            raise self.PoolBoutServiceError("找不到 'COMPLETED' 比赛状态")

        # 更新比赛
        updated_bout = self.bout_repository.update_bout_result(
            bout_id, fencer_a_score, fencer_b_score, winner_id
        )

        if not updated_bout:
            raise self.PoolBoutServiceError("更新比赛结果失败")

        return updated_bout

    def start_bout(self, bout_id: UUID) -> PoolBout:
        """开始比赛"""
        bout = self.bout_repository.get_bout_by_id(bout_id)
        if not bout:
            raise self.PoolBoutServiceError(f"比赛 {bout_id} 不存在")

        # 检查是否可以开始
        if bout.status_id != self.match_status_repository.get_by_code('READY').id:
            raise self.PoolBoutServiceError("比赛未准备就绪，无法开始")

        # 更新状态为进行中
        in_progress_status = self.match_status_repository.get_by_code('IN_PROGRESS')
        if not in_progress_status:
            raise self.PoolBoutServiceError("找不到 'IN_PROGRESS' 比赛状态")

        # 设置实际开始时间
        updated_bout = self.update_bout(bout_id, {
            'status_id': in_progress_status.id,
            'actual_start_time': datetime.now()
        })

        return updated_bout

    def complete_bout(self, bout_id: UUID, fencer_a_score: int, fencer_b_score: int) -> PoolBout:
        """完成比赛"""
        return self.update_bout_result(bout_id, fencer_a_score, fencer_b_score)

    def cancel_bout(self, bout_id: UUID, notes: Optional[str] = None) -> PoolBout:
        """取消比赛"""
        bout = self.bout_repository.get_bout_by_id(bout_id)
        if not bout:
            raise self.PoolBoutServiceError(f"比赛 {bout_id} 不存在")

        # 获取取消状态
        cancelled_status = self.match_status_repository.get_by_code('CANCELLED')
        if not cancelled_status:
            raise self.PoolBoutServiceError("找不到 'CANCELLED' 比赛状态")

        # 更新比赛
        updated_bout = self.update_bout(bout_id, {
            'status_id': cancelled_status.id,
            'notes': notes
        })

        return updated_bout

    def get_bout_stats(self, pool_id: UUID) -> Dict[str, Any]:
        """获取比赛统计"""
        return self.bout_repository.get_bout_stats(pool_id)

    def _validate_bout_data(self, data: dict, is_create: bool = True) -> None:
        """验证比赛数据"""
        errors = {}

        # 必填字段检查
        if is_create:
            required_fields = ['pool_id', 'fencer_a_id', 'fencer_b_id', 'status_id']
            for field in required_fields:
                if not data.get(field):
                    errors[field] = f"{field} 不能为空"

        # 验证运动员不能相同
        if data.get('fencer_a_id') and data.get('fencer_b_id'):
            if data['fencer_a_id'] == data['fencer_b_id']:
                errors['fencer_b_id'] = "运动员A和运动员B不能是同一人"

        # 比分验证
        if data.get('fencer_a_score') is not None and data.get('fencer_b_score') is not None:
            if data['fencer_a_score'] < 0 or data['fencer_b_score'] < 0:
                errors['fencer_a_score'] = "比分不能为负数"
                errors['fencer_b_score'] = "比分不能为负数"

        if errors:
            raise self.PoolBoutServiceError("数据验证失败", errors)

    def _validate_foreign_keys(self, data: dict) -> None:
        """验证外键存在性"""
        if 'pool_id' in data:
            pool = self.pool_repository.get_pool_by_id(data['pool_id'])
            if not pool:
                raise self.PoolBoutServiceError(f"小组 {data['pool_id']} 不存在")

        if 'fencer_a_id' in data:
            fencer_a = self.fencer_repository.get_fencer_by_id(data['fencer_a_id'])
            if not fencer_a:
                raise self.PoolBoutServiceError(f"运动员A {data['fencer_a_id']} 不存在")

        if 'fencer_b_id' in data:
            fencer_b = self.fencer_repository.get_fencer_by_id(data['fencer_b_id'])
            if not fencer_b:
                raise self.PoolBoutServiceError(f"运动员B {data['fencer_b_id']} 不存在")

        if 'status_id' in data:
            status = self.match_status_repository.get_by_id(data['status_id'])
            if not status:
                raise self.PoolBoutServiceError(f"比赛状态 {data['status_id']} 不存在")

        if 'winner_id' in data and data['winner_id']:
            winner = self.fencer_repository.get_fencer_by_id(data['winner_id'])
            if not winner:
                raise self.PoolBoutServiceError(f"获胜者 {data['winner_id']} 不存在")

    def _validate_status_transition(self, current_status_id: UUID, new_status_id: UUID) -> None:
        """验证状态转移是否有效"""
        if current_status_id == new_status_id:
            return

        # 这里可以添加状态转移验证逻辑
        # 例如：不能从COMPLETED状态转移到其他状态

        current_status = self.match_status_repository.get_by_id(current_status_id)
        new_status = self.match_status_repository.get_by_id(new_status_id)

        if not current_status or not new_status:
            return

        # 已完成的状态不能改变
        if current_status.status_code == 'COMPLETED':
            raise self.PoolBoutServiceError("已完成的比赛不能更改状态")

        # 已取消的状态不能改变（除非重新安排）
        if current_status.status_code == 'CANCELLED' and new_status.status_code != 'SCHEDULED':
            raise self.PoolBoutServiceError("已取消的比赛只能重新安排")

    def _validate_scores(self, fencer_a_score: int, fencer_b_score: int, bout: PoolBout) -> None:
        """验证比分"""
        errors = {}

        # 获取目标分数（从小组的规则中）
        pool = self.pool_repository.get_pool_by_id(bout.pool_id)
        if pool:
            # 这里需要获取小组对应的event和rule
            # 在实际实现中，需要查询数据库
            target_score = 5  # 默认5分
        else:
            target_score = 5

        # 比分不能为负数
        if fencer_a_score < 0 or fencer_b_score < 0:
            errors['scores'] = "比分不能为负数"

        # 比分不能超过目标分数
        if fencer_a_score > target_score or fencer_b_score > target_score:
            errors['scores'] = f"比分不能超过目标分数 {target_score}"

        # 不能同时为0（除非是弃权）
        if fencer_a_score == 0 and fencer_b_score == 0:
            errors['scores'] = "比分不能同时为0"

        if errors:
            raise self.PoolBoutServiceError("比分验证失败", errors)

    def _validate_winner(self, winner_id: UUID, fencer_a_id: UUID, fencer_b_id: UUID) -> None:
        """验证胜者"""
        if winner_id not in [fencer_a_id, fencer_b_id]:
            raise self.PoolBoutServiceError("胜者必须是比赛双方之一")

    def _get_pool_fencers(self, pool_id: UUID) -> List[UUID]:
        """获取小组成员（模拟实现）"""
        # 在实际实现中，这里应该调用PoolAssignment服务
        # 这里返回空列表，实际使用时需要实现
        return []

    class PoolBoutServiceError(Exception):
        """Service层异常"""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
