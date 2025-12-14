from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError

from core.models.pool import Pool
from core.constants.pool import PoolStatus, STATUS_TRANSITIONS, PoolLetter
from backend.apps.fencing_organizer.repositories.pool_repo import DjangoPoolRepository
from backend.apps.fencing_organizer.repositories.event_repo import DjangoEventRepository
from backend.apps.fencing_organizer.repositories.piste_repo import DjangoPisteRepository
# from backend.apps.fencing_organizer.repositories.event_seed_repo import DjangoEventSeedRepository
from backend.apps.fencing_organizer.repositories.fencer_repo import DjangoFencerRepository


class PoolService:
    """小组业务服务"""

    def __init__(self,
                 pool_repository: Optional[DjangoPoolRepository] = None,
                 event_repository: Optional[DjangoEventRepository] = None,
                 piste_repository: Optional[DjangoPisteRepository] = None,
                 # event_seed_repository: Optional[DjangoEventSeedRepository] = None
                 ):

        self.pool_repository = pool_repository or DjangoPoolRepository()
        self.event_repository = event_repository or DjangoEventRepository()
        self.piste_repository = piste_repository or DjangoPisteRepository()
        # self.event_seed_repository = event_seed_repository or DjangoEventSeedRepository()

    def get_pool_by_id(self, pool_id: UUID) -> Optional[Pool]:
        """根据ID获取小组"""
        return self.pool_repository.get_pool_by_id(pool_id)

    def get_pools_by_event(self, event_id: UUID) -> List[Pool]:
        """根据项目获取小组"""
        return self.pool_repository.get_pools_by_event(event_id)

    def get_active_pools(self) -> List[Pool]:
        """获取活跃的小组"""
        return self.pool_repository.get_active_pools()

    def get_pools_with_stats(self, event_id: UUID) -> List[Dict[str, Any]]:
        """获取小组及统计信息"""
        return self.pool_repository.get_pools_with_stats(event_id)

    def create_pool(self, pool_data: dict) -> Pool:
        """创建小组"""
        # 验证数据
        self._validate_pool_data(pool_data, is_create=True)

        # 验证外键存在性
        self._validate_foreign_keys(pool_data)

        # 如果未提供pool_number，自动生成
        if not pool_data.get('pool_number'):
            pool_data['pool_number'] = self.pool_repository.get_next_pool_number(
                pool_data['event_id']
            )

        # 创建Domain对象
        pool = Pool(**pool_data)

        # 通过Repository保存
        try:
            return self.pool_repository.save_pool(pool)
        except IntegrityError as e:
            if 'unique_pool_event_number' in str(e):
                raise self.PoolServiceError(f"小组编号 '{pool_data.get('pool_number')}' 在该项目中已存在")
            raise self.PoolServiceError(f"创建小组失败: {str(e)}")

    def create_pools_for_event(self, event_id: UUID, pool_count: int,
                               piste_id: Optional[UUID] = None) -> List[Pool]:
        """为项目创建多个小组"""
        # 验证项目存在
        event = self.event_repository.get_event_by_id(event_id)
        if not event:
            raise self.PoolServiceError(f"项目 {event_id} 不存在")

        # 验证剑道存在（如果提供）
        if piste_id:
            piste = self.piste_repository.get_by_id(piste_id)
            if not piste:
                raise self.PoolServiceError(f"剑道 {piste_id} 不存在")

        created_pools = []
        next_pool_number = self.pool_repository.get_next_pool_number(event_id)

        for i in range(pool_count):
            pool_data = {
                'event_id': event_id,
                'pool_number': next_pool_number + i,
                'pool_letter': self._number_to_letter(next_pool_number + i),
                'piste_id': piste_id,
                'status': PoolStatus.SCHEDULED.value
            }

            try:
                pool = self.create_pool(pool_data)
                created_pools.append(pool)
            except self.PoolServiceError as e:
                # 忽略单个小组创建失败，继续创建其他小组
                continue

        return created_pools

    def generate_balanced_pools(self, event_id: UUID, pool_size: int = 7) -> List[Pool]:
        """生成平衡的小组（随机分组）"""
        # 获取项目的参与者（这里需要从Event参与者获取）
        # 在MVP版本中，我们假设可以从Event获取参与者列表
        # 在实际实现中，需要根据Event的参与者关系获取

        # 方法1: 通过EventService获取参与者
        # from ...services.event_service import EventService
        # event_service = EventService()
        # participants = event_service.get_event_participants(event_id)

        # 方法2: 在MVP中，我们可以暂时返回空的参与者列表
        # 并创建一个简单的随机分组逻辑框架
        participants = self._get_event_participants(event_id)

        if not participants:
            raise self.PoolServiceError("项目没有参与者，无法生成小组")

        # 随机打乱参与者列表
        import random
        shuffled_participants = list(participants)
        random.shuffle(shuffled_participants)

        # 计算需要的小组数量
        participant_count = len(shuffled_participants)
        pool_count = (participant_count + pool_size - 1) // pool_size  # 向上取整

        # 创建分组
        groups = [[] for _ in range(pool_count)]

        # 均匀分配参与者到各小组
        for i, participant_id in enumerate(shuffled_participants):
            group_index = i % pool_count
            groups[group_index].append(participant_id)

        # 创建小组
        created_pools = []
        next_pool_number = self.pool_repository.get_next_pool_number(event_id)

        for i, group_members in enumerate(groups):
            if not group_members:
                continue

            pool_data = {
                'event_id': event_id,
                'pool_number': next_pool_number + i,
                'pool_letter': self._number_to_letter(next_pool_number + i),
                'status': PoolStatus.SCHEDULED.value
            }

            try:
                pool = self.create_pool(pool_data)

                # 创建小组成员分配（需要PoolAssignment服务）
                # 这里可以调用一个辅助方法来创建PoolAssignment
                self._create_pool_assignments(pool.id, group_members)

                created_pools.append(pool)
            except self.PoolServiceError as e:
                # 记录错误但继续创建其他小组
                print(f"创建小组失败: {e}")
                continue

        return created_pools

    def _get_event_participants(self, event_id: UUID) -> List[UUID]:
        """获取项目的参与者列表"""
        # 在MVP版本中，我们使用一个简化的方法获取参与者
        # 在实际应用中，这应该通过Event的参与者关系获取

        # 方法1: 如果已有Event参与者模型，直接查询
        # try:
        #     from ...models.event_participant import DjangoEventParticipant
        #     participants = DjangoEventParticipant.objects.filter(
        #         event_id=event_id
        #     ).values_list('fencer_id', flat=True)
        #     return list(participants)
        # except ImportError:
        #     pass

        # 方法2: 使用EventSeed表（如果有数据）
        # if self.event_seed_repository:
        #     try:
        #         seeds = self.event_seed_repository.get_seeds_by_event(event_id)
        #         return [seed.fencer_id for seed in seeds]
        #     except:
        #         pass

        # 方法3: 返回空列表，让调用者处理
        return []

    def _create_pool_assignments(self, pool_id: UUID, fencer_ids: List[UUID]) -> None:
        """创建小组成员分配"""
        # 这是一个辅助方法，用于创建PoolAssignment记录
        # 在MVP中，我们可以先实现一个简化的版本
        # 或者暂不实现，留待后续开发

        # 需要导入PoolAssignment模型和服务
        # from ...models.pool_assignment import DjangoPoolAssignment
        # for fencer_id in fencer_ids:
        #     DjangoPoolAssignment.objects.create(
        #         pool_id=pool_id,
        #         fencer_id=fencer_id,
        #         final_pool_rank=0,  # 初始排名设为0，后续计算
        #         victories=0,
        #         touches_scored=0,
        #         touches_received=0,
        #         matches_played=0,
        #         is_qualified=False
        #     )

        # 在MVP版本中，暂时只打印日志
        print(f"为小组 {pool_id} 分配了 {len(fencer_ids)} 名参与者")

    def update_pool(self, pool_id: UUID, pool_data: dict) -> Pool:
        """更新小组"""
        # 检查小组是否存在
        existing_pool = self.pool_repository.get_pool_by_id(pool_id)
        if not existing_pool:
            raise self.PoolServiceError(f"小组 {pool_id} 不存在")

        # 验证数据
        self._validate_pool_data(pool_data, is_create=False)

        # 验证状态转移
        if 'status' in pool_data and 'status' in pool_data:
            self._validate_status_transition(existing_pool.status, pool_data['status'])

        # 验证外键存在性
        self._validate_foreign_keys(pool_data)

        # 更新属性
        for key, value in pool_data.items():
            if hasattr(existing_pool, key):
                setattr(existing_pool, key, value)

        # 通过Repository保存
        try:
            return self.pool_repository.save_pool(existing_pool)
        except IntegrityError as e:
            if 'unique_pool_event_number' in str(e):
                raise self.PoolServiceError(f"小组编号 '{pool_data.get('pool_number')}' 在该项目中已存在")
            raise self.PoolServiceError(f"更新小组失败: {str(e)}")

    def update_pool_status(self, pool_id: UUID, status: str) -> Pool:
        """更新小组状态"""
        # 检查小组是否存在
        pool = self.pool_repository.get_pool_by_id(pool_id)
        if not pool:
            raise self.PoolServiceError(f"小组 {pool_id} 不存在")

        # 验证状态转移
        self._validate_status_transition(pool.status, status)

        # 更新状态
        updated_pool = self.pool_repository.update_pool_status(pool_id, status)
        if not updated_pool:
            raise self.PoolServiceError("更新小组状态失败")

        return updated_pool

    def assign_piste_to_pools(self, pool_ids: List[UUID], piste_id: UUID) -> List[Pool]:
        """为多个小组分配剑道"""
        # 验证剑道存在
        piste = self.piste_repository.get_by_id(piste_id)
        if not piste:
            raise self.PoolServiceError(f"剑道 {piste_id} 不存在")

        # 验证剑道可用
        if not piste.is_available:
            raise self.PoolServiceError(f"剑道 {piste_id} 不可用")

        # 分配剑道
        return self.pool_repository.assign_piste_to_pools(pool_ids, piste_id)

    def schedule_pools(self, pool_ids: List[UUID], start_time: datetime,
                       interval_minutes: int = 30) -> List[Pool]:
        """为多个小组安排时间"""
        scheduled_pools = []
        current_time = start_time

        for pool_id in pool_ids:
            try:
                pool = self.update_pool(pool_id, {
                    'start_time': current_time,
                    'status': PoolStatus.SCHEDULED.value
                })
                scheduled_pools.append(pool)
                current_time += timedelta(minutes=interval_minutes)
            except self.PoolServiceError:
                continue

        return scheduled_pools

    def _validate_pool_data(self, data: dict, is_create: bool = True) -> None:
        """验证小组数据"""
        errors = {}

        # 必填字段检查
        if is_create and not data.get('event_id'):
            errors['event_id'] = "event_id 不能为空"

        # 字段验证
        if data.get('pool_number') is not None and data['pool_number'] < 1:
            errors['pool_number'] = "小组编号必须大于0"

        if data.get('pool_letter') and len(data['pool_letter']) > 1:
            errors['pool_letter'] = "小组字母长度不能超过1个字符"

        # 状态验证
        if data.get('status'):
            valid_statuses = [status.value for status in PoolStatus]
            if data['status'] not in valid_statuses:
                errors['status'] = f"状态必须是: {', '.join(valid_statuses)}"

        if errors:
            raise self.PoolServiceError("数据验证失败", errors)

    def _validate_foreign_keys(self, data: dict) -> None:
        """验证外键存在性"""
        if 'event_id' in data:
            event = self.event_repository.get_event_by_id(data['event_id'])
            if not event:
                raise self.PoolServiceError(f"项目 {data['event_id']} 不存在")

        if 'piste_id' in data and data['piste_id']:
            piste = self.piste_repository.get_by_id(data['piste_id'])
            if not piste:
                raise self.PoolServiceError(f"剑道 {data['piste_id']} 不存在")

    def _validate_status_transition(self, current_status: str, new_status: str) -> None:
        """验证状态转移是否有效"""
        if current_status == new_status:
            return

        valid_transitions = STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in valid_transitions:
            raise self.PoolServiceError(
                f"无法从状态 '{current_status}' 转移到 '{new_status}'。"
                f"允许的转移: {', '.join(valid_transitions)}"
            )

    @staticmethod
    def _number_to_letter(number: int) -> str:
        """将数字转换为字母"""
        letters = []
        while number > 0:
            number, remainder = divmod(number - 1, 26)
            letters.append(chr(65 + remainder))
        return ''.join(reversed(letters)) if letters else "A"

    class PoolServiceError(Exception):
        """Service层异常"""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
