from rest_framework import serializers
from django.core.validators import MinLengthValidator
from .models import DjangoTournament


class TournamentSerializer(serializers.ModelSerializer):
    """赛事序列化器"""

    class Meta:
        model = DjangoTournament
        fields = [
            'id',
            'tournament_name',
            'organizer',
            'location',
            'start_date',
            'end_date',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_tournament_name(self, value):
        """验证赛事名称"""
        if len(value.strip()) == 0:
            raise serializers.ValidationError("赛事名称不能为空")

        if len(value) > 200:
            raise serializers.ValidationError("赛事名称长度不能超过200个字符")

        return value.strip()

    def validate_start_date(self, value):
        """验证开始日期"""
        # 可以添加业务规则，比如不能是过去日期等
        return value

    def validate_end_date(self, value):
        """验证结束日期"""
        # 验证将在validate方法中进行
        return value

    def validate(self, attrs):
        """整体验证"""
        errors = {}

        # 检查日期顺序
        if attrs.get('start_date') and attrs.get('end_date'):
            if attrs['end_date'] < attrs['start_date']:
                errors['end_date'] = "结束日期不能早于开始日期"

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def to_representation(self, instance):
        """处理输出数据"""
        representation = super().to_representation(instance)

        # 添加额外的统计信息
        representation['event_count'] = getattr(instance, 'event_count', 0)

        return representation


class TournamentCreateSerializer(serializers.ModelSerializer):
    """赛事创建序列化器"""

    class Meta:
        model = DjangoTournament
        fields = [
            'tournament_name',
            'organizer',
            'location',
            'start_date',
            'end_date',
            'status',
        ]

    def validate(self, attrs):
        if attrs.get('end_date') and attrs.get('start_date') and attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError({"end_date": "结束日期不能早于开始日期"})
        return attrs
