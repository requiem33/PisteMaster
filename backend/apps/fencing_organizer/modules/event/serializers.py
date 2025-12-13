from rest_framework import serializers
from django.core.validators import MinLengthValidator
from .models import DjangoEvent
from ..tournament.models import DjangoTournament
from ..rule.models import DjangoRule
from ..event_type.models import DjangoEventType
from ..event_status.models import DjangoEventStatus


class EventStatusSerializer(serializers.ModelSerializer):
    """项目状态序列化器"""

    class Meta:
        model = DjangoEventStatus
        fields = ['id', 'status_code', 'display_name']


class EventTypeSerializer(serializers.ModelSerializer):
    """项目类型序列化器"""

    # 计算字段
    is_individual = serializers.BooleanField(read_only=True)
    is_team = serializers.BooleanField(read_only=True)

    class Meta:
        model = DjangoEventType
        fields = ['id', 'type_code', 'display_name', 'weapon_type', 'gender', 'is_individual', 'is_team']


class EventSerializer(serializers.ModelSerializer):
    """比赛项目序列化器"""

    # 嵌套序列化器
    tournament = serializers.PrimaryKeyRelatedField(
        queryset=DjangoTournament.objects.all(),
        write_only=True,
        required=True
    )
    rule = serializers.PrimaryKeyRelatedField(
        queryset=DjangoRule.objects.all(),
        write_only=True,
        required=True
    )
    event_type = serializers.PrimaryKeyRelatedField(
        queryset=DjangoEventType.objects.all(),
        write_only=True,
        required=True
    )
    status = serializers.PrimaryKeyRelatedField(
        queryset=DjangoEventStatus.objects.all(),
        write_only=True,
        required=True
    )

    # 只读嵌套字段（用于输出）
    tournament_info = serializers.SerializerMethodField(read_only=True)
    rule_info = serializers.SerializerMethodField(read_only=True)
    event_type_info = serializers.SerializerMethodField(read_only=True)
    status_info = serializers.SerializerMethodField(read_only=True)

    # 计算字段
    participant_count = serializers.IntegerField(read_only=True)
    qualified_count = serializers.IntegerField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    weapon_type = serializers.CharField(read_only=True)
    gender = serializers.CharField(read_only=True)

    class Meta:
        model = DjangoEvent
        fields = [
            'id',
            'event_name',
            'tournament',
            'rule',
            'event_type',
            'status',
            'tournament_info',
            'rule_info',
            'event_type_info',
            'status_info',
            'is_team_event',
            'start_time',
            'participant_count',
            'qualified_count',
            'is_completed',
            'is_active',
            'weapon_type',
            'gender',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_team_event']

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

    def get_event_type_info(self, obj):
        """获取项目类型信息"""
        if obj.event_type:
            return {
                'id': str(obj.event_type.id),
                'type_code': obj.event_type.type_code,
                'display_name': obj.event_type.display_name,
                'weapon_type': obj.event_type.weapon_type,
                'gender': obj.event_type.gender
            }
        return None

    def get_status_info(self, obj):
        """获取状态信息"""
        if obj.status:
            return {
                'id': str(obj.status.id),
                'status_code': obj.status.status_code,
                'display_name': obj.status.display_name
            }
        return None

    def validate_event_name(self, value):
        """验证项目名称"""
        if len(value.strip()) == 0:
            raise serializers.ValidationError("项目名称不能为空")

        if len(value) > 200:
            raise serializers.ValidationError("项目名称长度不能超过200个字符")

        return value.strip()

    def validate(self, data):
        """整体验证"""
        errors = {}

        # 验证是否为团体赛与项目类型的一致性
        if 'event_type' in data and 'is_team_event' in data:
            event_type = data['event_type']
            if event_type.is_team != data['is_team_event']:
                errors[
                    'is_team_event'] = f"项目类型 {event_type.display_name} 应为{'团体赛' if event_type.is_team else '个人赛'}"

        # 验证赛事是否有效
        if 'tournament' in data:
            tournament = data['tournament']
            if not tournament.is_active:
                errors['tournament'] = "所选赛事非活跃状态，无法创建项目"

        # 验证开始时间是否在赛事时间范围内
        if 'start_time' in data and 'tournament' in data:
            start_time = data['start_time']
            tournament = data['tournament']

            if start_time:
                start_date = tournament.start_date
                end_date = tournament.end_date

                if start_time.date() < start_date:
                    errors['start_time'] = f"项目开始时间不能早于赛事开始日期 {start_date}"
                elif start_time.date() > end_date:
                    errors['start_time'] = f"项目开始时间不能晚于赛事结束日期 {end_date}"

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        """创建事件"""
        # 自动设置是否为团体赛
        validated_data['is_team_event'] = validated_data['event_type'].is_team
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """更新事件"""
        # 如果更新了event_type，自动更新is_team_event
        if 'event_type' in validated_data:
            validated_data['is_team_event'] = validated_data['event_type'].is_team
        return super().update(instance, validated_data)
