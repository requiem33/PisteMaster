from rest_framework import serializers
from django.core.validators import MinLengthValidator
from .models import DjangoEvent
from ..tournament.models import DjangoTournament
from ..rule.models import DjangoRule


class EventSerializer(serializers.ModelSerializer):
    """比赛项目序列化器"""

    # 嵌套序列化器
    tournament_id = serializers.PrimaryKeyRelatedField(
        queryset=DjangoTournament.objects.all(),
        source='tournament',
        write_only=True,
        required=True
    )
    rule_id = serializers.PrimaryKeyRelatedField(
        queryset=DjangoRule.objects.all(),
        source='rule',
        write_only=True,
        required=False,
        allow_null=True
    )

    # 只读嵌套字段（用于输出）
    tournament_info = serializers.SerializerMethodField(read_only=True)
    rule_info = serializers.SerializerMethodField(read_only=True)

    # 计算字段
    participant_count = serializers.IntegerField(read_only=True)
    qualified_count = serializers.IntegerField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = DjangoEvent
        fields = [
            'id',
            'event_name',
            'tournament_id',
            'rule_id',
            'event_type',
            'status',
            'current_step',
            'live_ranking',
            'de_trees',
            'tournament_info',
            'rule_info',
            'is_team_event',
            'start_time',
            'participant_count',
            'qualified_count',
            'is_completed',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_tournament_info(self, obj):
        """获取赛事信息"""
        if obj.tournament:
            return {
                'id': str(obj.tournament.id),
                'tournament_name': obj.tournament.tournament_name,
                'start_date': obj.tournament.start_date,
                'end_date': obj.tournament.end_date
            }
        return None

    def get_rule_info(self, obj):
        """获取规则信息"""
        if obj.rule:
            return {
                'id': str(obj.rule.id),
                'rule_name': obj.rule.rule_name,
                'pool_size': obj.rule.pool_size,
                'total_qualified_count': obj.rule.total_qualified_count
            }
        return None

    def validate_event_name(self, value):
        """验证项目名称"""
        if len(value.strip()) == 0:
            raise serializers.ValidationError("项目名称不能为空")

        if len(value) > 200:
            raise serializers.ValidationError("项目名称长度不能超过200个字符")

        return value.strip()

    def validate(self, attrs):
        """整体验证"""
        errors = {}

        # 验证开始时间是否在赛事时间范围内
        start_time = attrs.get('start_time')
        tournament = attrs.get('tournament')

        if start_time and tournament:
            start_date = tournament.start_date
            end_date = tournament.end_date

            if start_time.date() < start_date:
                errors['start_time'] = f"项目开始时间不能早于赛事开始日期 {start_date}"
            elif start_time.date() > end_date:
                errors['start_time'] = f"项目开始时间不能晚于赛事结束日期 {end_date}"

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

class EventCreateSerializer(serializers.ModelSerializer):
    """比赛项目创建序列化器"""
    class Meta:
        model = DjangoEvent
        fields = [
            'tournament_id',
            'event_name',
            'event_type',
            'rule_id',
            'is_team_event',
            'status'
        ]

