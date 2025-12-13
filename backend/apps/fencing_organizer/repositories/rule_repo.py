from typing import Optional, List
from uuid import UUID

from backend.apps.fencing_organizer.mappers.rule_mapper import RuleMapper
from backend.apps.fencing_organizer.modules.rule.models import DjangoRule
from core.interfaces.rule_repository import RuleRepositoryInterface
from core.models.rule import Rule


class DjangoRuleRepository(RuleRepositoryInterface):
    """赛制规则仓库的Django实现"""

    def get_rule_by_id(self, rule_id: UUID) -> Optional[Rule]:
        """通过ID获取规则"""
        try:
            django_rule = DjangoRule.objects.select_related(
                'elimination_type', 'final_ranking_type'
            ).get(pk=rule_id)
            return RuleMapper.to_domain(django_rule)
        except DjangoRule.DoesNotExist:
            return None

    def get_rule_by_name(self, rule_name: str) -> Optional[Rule]:
        """通过名称获取规则"""
        try:
            django_rule = DjangoRule.objects.select_related(
                'elimination_type', 'final_ranking_type'
            ).get(rule_name=rule_name)
            return RuleMapper.to_domain(django_rule)
        except DjangoRule.DoesNotExist:
            return None

    def get_all_rules(self) -> List[Rule]:
        """获取所有规则"""
        django_rules = DjangoRule.objects.select_related(
            'elimination_type', 'final_ranking_type'
        ).all().order_by('rule_name')

        return [RuleMapper.to_domain(r) for r in django_rules]

    def get_rules_by_elimination_type(self, elimination_type_id: UUID) -> List[Rule]:
        """根据淘汰赛类型获取规则"""
        django_rules = DjangoRule.objects.select_related(
            'elimination_type', 'final_ranking_type'
        ).filter(elimination_type_id=elimination_type_id).order_by('rule_name')

        return [RuleMapper.to_domain(r) for r in django_rules]

    def save_rule(self, rule: Rule) -> Rule:
        """保存或更新规则"""
        orm_data = RuleMapper.to_orm_data(rule)

        django_rule, created = DjangoRule.objects.update_or_create(
            id=rule.id,
            defaults=orm_data
        )

        return RuleMapper.to_domain(django_rule)

    def delete_rule(self, rule_id: UUID) -> bool:
        """删除规则"""
        try:
            # 检查是否有项目使用此规则
            from ..modules.event.models import DjangoEvent
            used_count = DjangoEvent.objects.filter(rule_id=rule_id).count()

            if used_count > 0:
                raise ValueError(f"无法删除，有 {used_count} 个项目正在使用此规则")

            count, _ = DjangoRule.objects.filter(id=rule_id).delete()
            return count > 0
        except ValueError as e:
            raise
        except Exception:
            return False

    def search_rules(self, **filters) -> List[Rule]:
        """搜索规则"""
        queryset = DjangoRule.objects.select_related(
            'elimination_type', 'final_ranking_type'
        )

        # 应用过滤器
        if 'name' in filters:
            queryset = queryset.filter(rule_name__icontains=filters['name'])
        if 'elimination_type_code' in filters:
            queryset = queryset.filter(elimination_type__type_code=filters['elimination_type_code'])
        if 'ranking_type_code' in filters:
            queryset = queryset.filter(final_ranking_type__type_code=filters['ranking_type_code'])
        if 'min_pool_size' in filters:
            queryset = queryset.filter(pool_size__gte=filters['min_pool_size'])
        if 'max_pool_size' in filters:
            queryset = queryset.filter(pool_size__lte=filters['max_pool_size'])

        # 排序
        ordering = filters.get('ordering', 'rule_name')
        if ordering:
            queryset = queryset.order_by(ordering)

        return [RuleMapper.to_domain(r) for r in queryset]
