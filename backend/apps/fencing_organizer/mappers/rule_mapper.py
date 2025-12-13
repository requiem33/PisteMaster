from backend.apps.fencing_organizer.modules.rule.models import DjangoRule
from core.models.rule import Rule


class RuleMapper:
    """赛制规则映射器"""

    @staticmethod
    def to_domain(django_rule: DjangoRule) -> Rule:
        """Django ORM → Core Domain"""
        return Rule(
            id=django_rule.id,
            rule_name=django_rule.rule_name,
            total_qualified_count=django_rule.total_qualified_count,
            elimination_type_id=django_rule.elimination_type.id,
            final_ranking_type_id=django_rule.final_ranking_type.id,
            match_format=django_rule.match_format,
            pool_size=django_rule.pool_size,
            match_duration=django_rule.match_duration,
            match_score_pool=django_rule.match_score_pool,
            match_score_elimination=django_rule.match_score_elimination,
            group_qualification_ratio=django_rule.group_qualification_ratio,
            description=django_rule.description
        )

    @staticmethod
    def to_orm_data(rule: Rule) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": rule.id,
            "rule_name": rule.rule_name,
            "total_qualified_count": rule.total_qualified_count,
            "elimination_type_id": rule.elimination_type_id,
            "final_ranking_type_id": rule.final_ranking_type_id,
            "match_format": rule.match_format,
            "pool_size": rule.pool_size,
            "match_duration": rule.match_duration,
            "match_score_pool": rule.match_score_pool,
            "match_score_elimination": rule.match_score_elimination,
            "group_qualification_ratio": rule.group_qualification_ratio,
            "description": rule.description
        }
