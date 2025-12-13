from rest_framework import serializers
from decimal import Decimal
from .models import DjangoRule
from backend.apps.fencing_organizer.modules.elimination_type.models import DjangoEliminationType
from backend.apps.fencing_organizer.modules.ranking_type.models import DjangoRankingType


class EliminationTypeSerializer(serializers.ModelSerializer):
    """淘汰赛类型序列化器"""

    class Meta:
        model = DjangoEliminationType
        fields = ['id', 'type_code', 'display_name']


class RankingTypeSerializer(serializers.ModelSerializer):
    """排名类型序列化器"""

    class Meta:
        model = DjangoRankingType
        fields = ['id', 'type_code', 'display_name']


class RuleSerializer(serializers.ModelSerializer):
    """赛制规则序列化器"""

    # 嵌套序列化器
    elimination_type = EliminationTypeSerializer(read_only=True)
    final_ranking_type = RankingTypeSerializer(read_only=True)

    # 计算字段
    elimination_type_code = serializers.CharField(source='elimination_type.type_code', read_only=True)
    ranking_type_code = serializers.CharField(source='final_ranking_type.type_code', read_only=True)

    class Meta:
        model = DjangoRule
        fields = [
            'id',
            'rule_name',
            'elimination_type',
            'final_ranking_type',
            'elimination_type_code',
            'ranking_type_code',
            'match_format',
            'pool_size',
            'match_duration',
            'match_score_pool',
            'match_score_elimination',
            'total_qualified_count',
            'group_qualification_ratio',
            'description',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_rule_name(self, value):
        """验证规则名称"""
        if len(value.strip()) == 0:
            raise serializers.ValidationError("规则名称不能为空")

        if len(value) > 100:
            raise serializers.ValidationError("规则名称长度不能超过100个字符")

        # 检查是否已存在（更新时排除自己）
        instance = self.instance
        if instance and instance.rule_name == value:
            return value

        if DjangoRule.objects.filter(rule_name=value).exists():
            raise serializers.ValidationError(f"规则名称 '{value}' 已存在")

        return value.strip()

    def validate_pool_size(self, value):
        """验证小组人数"""
        if value is not None and value < 3:
            raise serializers.ValidationError("小组赛每组人数至少为3人")
        return value

    def validate_total_qualified_count(self, value):
        """验证总晋级人数"""
        if value < 1:
            raise serializers.ValidationError("总晋级人数必须大于0")
        return value

    def validate_group_qualification_ratio(self, value):
        """验证晋级比例"""
        if value is not None:
            try:
                ratio = Decimal(str(value))
                if ratio < 0 or ratio > 1:
                    raise serializers.ValidationError("晋级比例必须在0和1之间")
            except (ValueError, TypeError):
                raise serializers.ValidationError("晋级比例必须是有效的小数")
        return value

    def validate(self, data):
        """整体验证"""
        errors = {}

        # 检查pool_size和group_qualification_ratio的关系
        if data.get('pool_size') and data.get('group_qualification_ratio'):
            pool_size = data['pool_size']
            ratio = data['group_qualification_ratio']
            qualified_count = int(pool_size * ratio)

            if qualified_count < 1:
                errors['group_qualification_ratio'] = f"晋级比例过小，至少应有1人晋级"

        # 检查match_score_pool和match_score_elimination
        if data.get('match_score_pool') and data.get('match_score_elimination'):
            if data['match_score_pool'] > data['match_score_elimination']:
                errors['match_score_pool'] = "小组赛目标分数不能大于淘汰赛目标分数"

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def to_internal_value(self, data):
        """处理输入数据"""
        # 将elimination_type_id转换为elimination_type（外键对象）
        if 'elimination_type_id' in data:
            try:
                data['elimination_type'] = DjangoEliminationType.objects.get(
                    pk=data.pop('elimination_type_id')
                )
            except DjangoEliminationType.DoesNotExist:
                raise serializers.ValidationError({
                    'elimination_type_id': "指定的淘汰赛类型不存在"
                })

        # 将final_ranking_type_id转换为final_ranking_type（外键对象）
        if 'final_ranking_type_id' in data:
            try:
                data['final_ranking_type'] = DjangoRankingType.objects.get(
                    pk=data.pop('final_ranking_type_id')
                )
            except DjangoRankingType.DoesNotExist:
                raise serializers.ValidationError({
                    'final_ranking_type_id': "指定的排名类型不存在"
                })

        return super().to_internal_value(data)


class RuleCreateSerializer(RuleSerializer):
    """规则创建序列化器"""

    # 创建时需要提供外键ID
    elimination_type_id = serializers.UUIDField(write_only=True, required=True)
    final_ranking_type_id = serializers.UUIDField(write_only=True, required=True)

    class Meta(RuleSerializer.Meta):
        fields = RuleSerializer.Meta.fields + ['elimination_type_id', 'final_ranking_type_id']

    def to_internal_value(self, data):
        """重写以处理外键ID"""
        return super(RuleSerializer, self).to_internal_value(data)