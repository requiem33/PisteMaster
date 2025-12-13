from typing import List, Optional
from uuid import UUID
from django.db import IntegrityError

from core.models.tournament_status import TournamentStatus
from backend.apps.fencing_organizer.repositories.tournament_status_repo import DjangoTournamentStatusRepository
from core.constants.tournament_status import PREDEFINED_STATUSES


class TournamentStatusService:
    """赛事状态业务服务"""

    def __init__(self, repository: Optional[DjangoTournamentStatusRepository] = None):
        self.repository = repository or DjangoTournamentStatusRepository()

    def get_status_by_id(self, status_id: UUID) -> Optional[TournamentStatus]:
        """根据ID获取状态"""
        return self.repository.get_status_by_id(status_id)

    def get_status_by_code(self, status_code: str) -> Optional[TournamentStatus]:
        """根据代码获取状态"""
        return self.repository.get_status_by_code(status_code)

    def get_all_statuses(self) -> List[TournamentStatus]:
        """获取所有状态"""
        return self.repository.get_all_statuses()

    def create_status(self, status_data: dict) -> TournamentStatus:
        """创建新状态"""
        # 验证数据
        self._validate_status_data(status_data)

        # 创建Domain对象
        status = TournamentStatus(**status_data)

        # 通过Repository保存
        try:
            return self.repository.save_status(status)
        except IntegrityError as e:
            raise self.TournamentStatusServiceError(f"状态代码 '{status_data.get('status_code')}' 已存在")

    def update_status(self, status_id: UUID, status_data: dict) -> TournamentStatus:
        """更新状态"""
        # 检查状态是否存在
        existing_status = self.repository.get_status_by_id(status_id)
        if not existing_status:
            raise self.TournamentStatusServiceError(f"状态 {status_id} 不存在")

        # 验证数据
        self._validate_status_data(status_data, is_update=True)

        # 更新属性
        for key, value in status_data.items():
            if hasattr(existing_status, key):
                setattr(existing_status, key, value)

        # 通过Repository保存
        try:
            return self.repository.save_status(existing_status)
        except IntegrityError as e:
            raise self.TournamentStatusServiceError(f"状态代码 '{status_data.get('status_code')}' 已存在")

    def initialize_predefined_statuses(self) -> List[TournamentStatus]:
        """初始化预定义状态"""
        created_statuses = []

        for status_data in PREDEFINED_STATUSES:
            try:
                # 检查是否已存在
                existing = self.repository.get_status_by_code(status_data['status_code'])
                if existing:
                    continue

                # 创建状态
                status = self.create_status(status_data)
                created_statuses.append(status)
            except self.TournamentStatusServiceError:
                # 忽略重复状态
                continue

        return created_statuses

    def _validate_status_data(self, data: dict, is_update: bool = False) -> None:
        """验证状态数据"""
        errors = {}

        # 必填字段检查
        if not data.get('status_code'):
            errors['status_code'] = "状态代码不能为空"
        elif len(data['status_code']) > 20:
            errors['status_code'] = "状态代码长度不能超过20个字符"

        # 可选字段长度检查
        if data.get('display_name') and len(data['display_name']) > 50:
            errors['display_name'] = "显示名称长度不能超过50个字符"

        if data.get('description') and len(data['description']) > 200:
            errors['description'] = "描述长度不能超过200个字符"

        if errors:
            raise self.TournamentStatusServiceError("数据验证失败", errors)

    class TournamentStatusServiceError(Exception):
        """Service层异常"""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
