from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal, InvalidOperation
from django.db import IntegrityError, transaction

from core.models.rule import Rule
from backend.apps.fencing_organizer.repositories.rule_repo import DjangoRuleRepository
from backend.apps.fencing_organizer.repositories.elimination_type_repo import DjangoEliminationTypeRepository
from backend.apps.fencing_organizer.repositories.ranking_type_repo import DjangoRankingTypeRepository
from core.constants.rules import (
    PREDEFINED_RULES,
    PREDEFINED_ELIMINATION_TYPES,
    PREDEFINED_RANKING_TYPES
)


class RuleService:
    """赛制规则业务服务"""

    def __init__(self,
                 rule_repository: Optional[DjangoRuleRepository] = None,
                 elimination_type_repo: Optional[DjangoEliminationTypeRepository] = None,
                 ranking_type_repo: Optional[DjangoRankingTypeRepository] = None):

        self.rule_repository = rule_repository or DjangoRuleRepository()
        self.elimination_type_repo = elimination_type_repo or DjangoEliminationTypeRepository()
        self.ranking_type_repo = ranking_type_repo or DjangoRankingTypeRepository()

    def get_rule_by_id(self, rule_id: UUID) -> Optional[Rule]:
        """根据ID获取规则"""
        return self.rule_repository.get_rule_by_id(rule_id)

    def get_rule_by_name(self, rule_name: str) -> Optional[Rule]:
        """根据名称获取规则"""
        return self.rule_repository.get_rule_by_name(rule_name)

    def get_all_rules(self) -> List[Rule]:
        """获取所有规则"""
        return self.rule_repository.get_all_rules()

    def get_rules_by_elimination_type(self, elimination_type_id: UUID) -> List[Rule]:
        """根据淘汰赛类型获取规则"""
        return self.rule_repository.get_rules_by_elimination_type(elimination_type_id)

    def create_rule(self, rule_data: dict) -> Rule:
        """创建规则"""
        # 验证数据
        self._validate_rule_data(rule_data, is_create=True)

        # 验证外键存在性
        self._validate_foreign_keys(rule_data)

        # 创建Domain对象
        rule = Rule(**rule_data)

        # 通过Repository保存
        try:
            return self.rule_repository.save_rule(rule)
        except IntegrityError as e:
            raise self.RuleServiceError(f"创建规则失败: {str(e)}")

    def update_rule(self, rule_id: UUID, rule_data: dict) -> Rule:
        """更新规则"""
        # 检查规则是否存在
        existing_rule = self.rule_repository.get_rule_by_id(rule_id)
        if not existing_rule:
            raise self.RuleServiceError(f"规则 {rule_id} 不存在")

        # 验证数据
        self._validate_rule_data(rule_data, is_create=False)

        # 验证外键存在性
        self._validate_foreign_keys(rule_data)

        # 更新属性
        for key, value in rule_data.items():
            if hasattr(existing_rule, key):
                setattr(existing_rule, key, value)

        # 通过Repository保存
        try:
            return self.rule_repository.save_rule(existing_rule)
        except IntegrityError as e:
            raise self.RuleServiceError(f"更新规则失败: {str(e)}")

    def delete_rule(self, rule_id: UUID) -> bool:
        """删除规则"""
        try:
            return self.rule_repository.delete_rule(rule_id)
        except ValueError as e:
            raise self.RuleServiceError(str(e))

    def search_rules(self, **filters) -> List[Rule]:
        """搜索规则"""
        return self.rule_repository.search_rules(**filters)

    def initialize_predefined_data(self) -> Dict[str, int]:
        """初始化预定义数据（淘汰赛类型、排名类型、规则）"""
        results = {
            "elimination_types": 0,
            "ranking_types": 0,
            "rules": 0
        }

        # 初始化淘汰赛类型
        for type_data in PREDEFINED_ELIMINATION_TYPES:
            try:
                existing = self.elimination_type_repo.get_by_code(type_data['type_code'])
                if existing:
                    continue

                elimination_type = self.elimination_type_repo.save(
                    EliminationType(**type_data)
                )
                results["elimination_types"] += 1
            except Exception:
                continue

        # 初始化排名类型
        for type_data in PREDEFINED_RANKING_TYPES:
            try:
                existing = self.ranking_type_repo.get_by_code(type_data['type_code'])
                if existing:
                    continue

                ranking_type = self.ranking_type_repo.save(
                    RankingType(**type_data)
                )
                results["ranking_types"] += 1
            except Exception:
                continue

        # 初始化规则
        for rule_data in PREDEFINED_RULES:
            try:
                # 获取外键ID
                elimination_type = self.elimination_type_repo.get_by_code(
                    rule_data['elimination_type_code']
                )
                ranking_type = self.ranking_type_repo.get_by_code(
                    rule_data['final_ranking_type_code']
                )

                if not elimination_type or not ranking_type:
                    continue

                # 检查是否已存在
                existing = self.rule_repository.get_rule_by_name(rule_data['rule_name'])
                if existing:
                    continue

                # 准备规则数据
                rule_create_data = {
                    "rule_name": rule_data['rule_name'],
                    "total_qualified_count": rule_data['total_qualified_count'],
                    "elimination_type_id": elimination_type.id,
                    "final_ranking_type_id": ranking_type.id,
                    "match_format": rule_data.get('match_format'),
                    "pool_size": rule_data.get('pool_size'),
                    "match_duration": rule_data.get('match_duration'),
                    "match_score_pool": rule_data.get('match_score_pool'),
                    "match_score_elimination": rule_data.get('match_score_elimination'),
                    "group_qualification_ratio": rule_data.get('group_qualification_ratio'),
                    "description": rule_data.get('description')
                }

                # 创建规则
                rule = self.create_rule(rule_create_data)
                results["rules"] += 1
            except self.RuleServiceError:
                # 忽略重复规则
                continue

        return results

    def _validate_rule_data(self, data: dict, is_create: bool = True) -> None:
        """验证规则数据"""
        errors = {}

        # 必填字段检查
        if is_create:
            required_fields = ['rule_name', 'total_qualified_count',
                               'elimination_type_id', 'final_ranking_type_id']
            for field in required_fields:
                if not data.get(field):
                    errors[field] = f"{field} 不能为空"

        # 字段长度验证
        if data.get('rule_name') and len(data['rule_name']) > 100:
            errors['rule_name'] = "规则名称长度不能超过100个字符"

        if data.get('match_format') and len(data['match_format']) > 50:
            errors['match_format'] = "比赛格式长度不能超过50个字符"

        # 数值验证
        if data.get('total_qualified_count') is not None:
            if data['total_qualified_count'] < 1:
                errors['total_qualified_count'] = "总晋级人数必须大于0"

        if data.get('pool_size') is not None:
            if data['pool_size'] < 3:
                errors['pool_size'] = "小组赛每组人数至少为3人"

        if data.get('match_duration') is not None:
            if data['match_duration'] < 30:  # 至少30秒
                errors['match_duration'] = "单局时长至少为30秒"

        if data.get('match_score_pool') is not None:
            if data['match_score_pool'] < 1:
                errors['match_score_pool'] = "小组赛目标分数必须大于0"

        if data.get('match_score_elimination') is not None:
            if data['match_score_elimination'] < 1:
                errors['match_score_elimination'] = "淘汰赛目标分数必须大于0"

        if data.get('group_qualification_ratio') is not None:
            try:
                ratio = Decimal(str(data['group_qualification_ratio']))
                if ratio < 0 or ratio > 1:
                    errors['group_qualification_ratio'] = "晋级比例必须在0和1之间"
            except (InvalidOperation, TypeError, ValueError):
                errors['group_qualification_ratio'] = "晋级比例必须是有效的小数"

        if errors:
            raise self.RuleServiceError("数据验证失败", errors)

    def _validate_foreign_keys(self, data: dict) -> None:
        """验证外键存在性"""
        if 'elimination_type_id' in data:
            elimination_type = self.elimination_type_repo.get_by_id(data['elimination_type_id'])
            if not elimination_type:
                raise self.RuleServiceError(f"淘汰赛类型 {data['elimination_type_id']} 不存在")

        if 'final_ranking_type_id' in data:
            ranking_type = self.ranking_type_repo.get_by_id(data['final_ranking_type_id'])
            if not ranking_type:
                raise self.RuleServiceError(f"排名类型 {data['final_ranking_type_id']} 不存在")

    class RuleServiceError(Exception):
        """Service层异常"""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
