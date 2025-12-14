from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import date, datetime
from django.db import IntegrityError
import re

from core.models.fencer import Fencer
from backend.apps.fencing_organizer.repositories.fencer_repo import DjangoFencerRepository


class FencerService:
    """Fencer业务服务"""

    def __init__(self, repository: Optional[DjangoFencerRepository] = None):
        self.repository = repository or DjangoFencerRepository()

    def get_fencer_by_id(self, fencer_id: UUID) -> Optional[Fencer]:
        """根据ID获取运动员"""
        return self.repository.get_fencer_by_id(fencer_id)

    def get_fencer_by_fencing_id(self, fencing_id: str) -> Optional[Fencer]:
        """根据击剑ID获取运动员"""
        return self.repository.get_fencer_by_fencing_id(fencing_id)

    def create_fencer(self, fencer_data: dict) -> Fencer:
        """创建运动员"""
        # 验证数据
        self._validate_fencer_data(fencer_data, is_create=True)

        # 创建Domain对象
        fencer = Fencer(**fencer_data)

        # 自动生成display_name（如果没有提供）
        if not fencer.display_name:
            fencer.display_name = f"{fencer.last_name} {fencer.first_name}"

        # 通过Repository保存
        try:
            return self.repository.save_fencer(fencer)
        except IntegrityError as e:
            if 'unique' in str(e).lower() and 'fencing_id' in str(e):
                raise self.FencerServiceError(f"击剑ID '{fencer_data.get('fencing_id')}' 已存在")
            raise self.FencerServiceError(f"创建运动员失败: {str(e)}")

    def update_fencer(self, fencer_id: UUID, fencer_data: dict) -> Fencer:
        """更新运动员"""
        # 检查运动员是否存在
        existing_fencer = self.repository.get_fencer_by_id(fencer_id)
        if not existing_fencer:
            raise self.FencerServiceError(f"运动员 {fencer_id} 不存在")

        # 验证数据
        self._validate_fencer_data(fencer_data, is_create=False)

        # 检查击剑ID是否重复（如果要更新fencing_id）
        if 'fencing_id' in fencer_data and fencer_data['fencing_id']:
            existing_with_fencing_id = self.repository.get_fencer_by_fencing_id(fencer_data['fencing_id'])
            if existing_with_fencing_id and existing_with_fencing_id.id != fencer_id:
                raise self.FencerServiceError(f"击剑ID '{fencer_data['fencing_id']}' 已被其他运动员使用")

        # 更新属性
        for key, value in fencer_data.items():
            if hasattr(existing_fencer, key):
                setattr(existing_fencer, key, value)

        # 自动更新updated_at时间
        existing_fencer.updated_at = datetime.now()

        # 通过Repository保存
        try:
            return self.repository.save_fencer(existing_fencer)
        except IntegrityError as e:
            if 'unique' in str(e).lower() and 'fencing_id' in str(e):
                raise self.FencerServiceError(f"击剑ID '{fencer_data.get('fencing_id')}' 已被其他运动员使用")
            raise self.FencerServiceError(f"更新运动员失败: {str(e)}")

    def delete_fencer(self, fencer_id: UUID) -> bool:
        """删除运动员"""
        # 检查运动员是否存在
        fencer = self.repository.get_fencer_by_id(fencer_id)
        if not fencer:
            raise self.FencerServiceError(f"运动员 {fencer_id} 不存在")

        # 检查是否有依赖关系（例如是否参与了比赛）
        # 这里可以添加检查逻辑

        return self.repository.delete_fencer(fencer_id)

    def search_fencers(self, query: str, limit: int = 50) -> List[Fencer]:
        """搜索运动员"""
        if not query or len(query.strip()) < 1:
            raise self.FencerServiceError("搜索词不能为空")

        return self.repository.search_fencers(query.strip(), limit)

    def get_fencers_by_country(self, country_code: str) -> List[Fencer]:
        """根据国家获取运动员"""
        if not country_code or len(country_code) != 3:
            raise self.FencerServiceError("国家代码必须是3个字母")

        return self.repository.get_fencers_by_country(country_code)

    def get_fencers_by_weapon(self, weapon: str) -> List[Fencer]:
        """根据剑种获取运动员"""
        valid_weapons = ['FOIL', 'EPEE', 'SABRE', None]
        if weapon.upper() not in valid_weapons:
            raise self.FencerServiceError(f"剑种必须是: {', '.join([w for w in valid_weapons if w])}")

        return self.repository.get_fencers_by_weapon(weapon.upper())

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.repository.count_fencers()

    def _validate_fencer_data(self, data: dict, is_create: bool = True) -> None:
        """验证运动员数据"""
        errors = {}

        # 必填字段检查
        if is_create:
            required_fields = ['first_name', 'last_name']
            for field in required_fields:
                if not data.get(field):
                    errors[field] = f"{field} 不能为空"

        # 字段长度验证
        if 'first_name' in data and data['first_name'] and len(data['first_name']) > 100:
            errors['first_name'] = "名长度不能超过100个字符"

        if 'last_name' in data and data['last_name'] and len(data['last_name']) > 100:
            errors['last_name'] = "姓长度不能超过100个字符"

        if 'display_name' in data and data['display_name'] and len(data['display_name']) > 200:
            errors['display_name'] = "显示名称长度不能超过200个字符"

        if 'fencing_id' in data and data['fencing_id'] and len(data['fencing_id']) > 50:
            errors['fencing_id'] = "击剑ID长度不能超过50个字符"

        # 国家代码验证
        if 'country_code' in data and data['country_code']:
            if len(data['country_code']) != 3:
                errors['country_code'] = "国家代码必须是3个字母"
            elif not data['country_code'].isalpha():
                errors['country_code'] = "国家代码只能包含字母"

        # 性别验证
        valid_genders = ['MEN', 'WOMEN', 'MIXED', 'OPEN', None]
        if 'gender' in data and data['gender'] not in valid_genders:
            errors['gender'] = f"性别必须是: {', '.join([g for g in valid_genders if g])}"

        # 剑种验证
        valid_weapons = ['FOIL', 'EPEE', 'SABRE', None]
        if 'primary_weapon' in data and data['primary_weapon'] not in valid_weapons:
            errors['primary_weapon'] = f"剑种必须是: {', '.join([w for w in valid_weapons if w])}"

        # 排名验证
        if 'current_ranking' in data and data['current_ranking'] is not None:
            if not isinstance(data['current_ranking'], int):
                errors['current_ranking'] = "排名必须是整数"
            elif data['current_ranking'] < 0:
                errors['current_ranking'] = "排名不能为负数"

        # 出生日期验证
        if 'birth_date' in data and data['birth_date']:
            if isinstance(data['birth_date'], str):
                try:
                    # 尝试解析日期字符串
                    from datetime import datetime as dt
                    birth_date = dt.strptime(data['birth_date'], '%Y-%m-%d').date()
                    data['birth_date'] = birth_date

                    # 检查是否在合理范围内
                    if birth_date > date.today():
                        errors['birth_date'] = "出生日期不能晚于今天"
                    elif birth_date.year < 1900:
                        errors['birth_date'] = "出生日期不能早于1900年"
                except ValueError:
                    errors['birth_date'] = "出生日期格式应为 YYYY-MM-DD"
            elif isinstance(data['birth_date'], date):
                # 已经是date对象，直接检查
                if data['birth_date'] > date.today():
                    errors['birth_date'] = "出生日期不能晚于今天"
                elif data['birth_date'].year < 1900:
                    errors['birth_date'] = "出生日期不能早于1900年"

        if errors:
            raise self.FencerServiceError("数据验证失败", errors)

    class FencerServiceError(Exception):
        """Service层异常"""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
