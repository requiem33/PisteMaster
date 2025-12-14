from typing import List, Optional, Dict, Any
from uuid import UUID
from django.db import IntegrityError, transaction

from core.models.piste import Piste
from backend.apps.fencing_organizer.repositories.piste_repo import DjangoPisteRepository
from backend.apps.fencing_organizer.repositories.tournament_repo import DjangoTournamentRepository


class PisteService:
    """剑道业务服务"""

    def __init__(self, repository: Optional[DjangoPisteRepository] = None):
        self.repository = repository or DjangoPisteRepository()
        self.tournament_repository = DjangoTournamentRepository()

    def get_piste_by_id(self, piste_id: UUID) -> Optional[Piste]:
        """根据ID获取剑道"""
        return self.repository.get_by_id(piste_id)

    def get_pistes_by_tournament(self, tournament_id: UUID) -> List[Piste]:
        """根据赛事获取剑道"""
        return self.repository.get_by_tournament(tournament_id)

    def get_available_pistes(self, tournament_id: UUID) -> List[Piste]:
        """获取可用的剑道"""
        return self.repository.get_available_pistes(tournament_id)

    def create_piste(self, piste_data: dict) -> Piste:
        """创建剑道"""
        # 验证数据
        self._validate_piste_data(piste_data)

        # 验证赛事存在
        tournament = self.tournament_repository.get_tournament_by_id(piste_data.get('tournament_id'))
        if not tournament:
            raise self.PisteServiceError(f"赛事 {piste_data.get('tournament_id')} 不存在")

        # 创建Domain对象
        piste = Piste(**piste_data)

        # 通过Repository保存
        try:
            return self.repository.save(piste)
        except IntegrityError as e:
            if 'unique_piste_tournament_number' in str(e):
                raise self.PisteServiceError(f"剑道编号 '{piste_data.get('piste_number')}' 在该赛事中已存在")
            raise self.PisteServiceError(f"创建剑道失败: {str(e)}")

    def update_piste(self, piste_id: UUID, piste_data: dict) -> Piste:
        """更新剑道"""
        # 检查剑道是否存在
        existing_piste = self.repository.get_by_id(piste_id)
        if not existing_piste:
            raise self.PisteServiceError(f"剑道 {piste_id} 不存在")

        # 验证数据
        self._validate_piste_data(piste_data, is_update=True)

        # 更新属性
        for key, value in piste_data.items():
            if hasattr(existing_piste, key):
                setattr(existing_piste, key, value)

        # 通过Repository保存
        try:
            return self.repository.save(existing_piste)
        except IntegrityError as e:
            if 'unique_piste_tournament_number' in str(e):
                raise self.PisteServiceError(f"剑道编号 '{piste_data.get('piste_number')}' 在该赛事中已存在")
            raise self.PisteServiceError(f"更新剑道失败: {str(e)}")

    def _validate_piste_data(self, data: dict, is_update: bool = False) -> None:
        """验证剑道数据"""
        errors = {}

        # 必填字段检查
        if is_update:
            required_fields = ['piste_number', 'tournament_id']
        else:
            required_fields = ['piste_number', 'tournament_id']

        for field in required_fields:
            if not data.get(field):
                errors[field] = f"{field} 不能为空"

        # 字段长度验证
        if data.get('piste_number') and len(data['piste_number']) > 10:
            errors['piste_number'] = "剑道编号长度不能超过10个字符"

        if data.get('location') and len(data['location']) > 100:
            errors['location'] = "具体位置长度不能超过100个字符"

        if data.get('piste_type') and len(data['piste_type']) > 20:
            errors['piste_type'] = "剑道类型长度不能超过20个字符"

        # 剑道类型验证
        valid_piste_types = ['MAIN', 'SIDE', 'WARMUP', None]
        if data.get('piste_type') not in valid_piste_types:
            errors['piste_type'] = f"剑道类型必须是: {', '.join([t for t in valid_piste_types if t])}"

        if errors:
            raise self.PisteServiceError("数据验证失败", errors)

    class PisteServiceError(Exception):
        """Service层异常"""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
