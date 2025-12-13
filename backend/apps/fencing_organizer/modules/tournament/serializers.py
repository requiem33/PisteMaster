from rest_framework import serializers
from django.core.validators import MinLengthValidator
from .models import DjangoTournament
from ..tournament_status.models import DjangoTournamentStatus


class TournamentSerializer(serializers.ModelSerializer):
    """赛事序列化器"""

    # 自定义字段
    status_display = serializers.CharField(source='status.display_name', read_only=True)
    status_code = serializers.CharField(source='status.status_code', read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = DjangoTournament
        fields = [
            'id',
            'tournament_name',
            'organizer',
            'location',
            'start_date',
            'end_date',
            'status',  # 外键ID
            'status_display',  # 显示名称
            'status_code',  # 状态代码
            'duration_days',
            'is_active',
            'created_at',
            'updated_at'
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

    def validate(self, data):
        """整体验证"""
        errors = {}

        # 检查日期顺序
        if data.get('start_date') and data.get('end_date'):
            if data['end_date'] < data['start_date']:
                errors['end_date'] = "结束日期不能早于开始日期"

        # 检查状态是否存在（如果提供了）
        if 'status' in data:
            try:
                status = DjangoTournamentStatus.objects.get(pk=data['status'])
            except DjangoTournamentStatus.DoesNotExist:
                errors['status'] = "指定的状态不存在"

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def to_internal_value(self, data):
        """处理输入数据"""
        # 将status_id转换为status（外键对象）
        if 'status_id' in data:
            data['status'] = data.pop('status_id')

        return super().to_internal_value(data)

    def to_representation(self, instance):
        """处理输出数据"""
        representation = super().to_representation(instance)

        # 添加额外的统计信息
        representation['event_count'] = getattr(instance, 'event_count', 0)

        return representation


class TournamentCreateSerializer(TournamentSerializer):
    """赛事创建序列化器（可以有不同的验证规则）"""

    class Meta(TournamentSerializer.Meta):
        pass

    def validate_status(self, value):
        """创建时验证状态"""
        # 创建时只允许特定的初始状态
        allowed_initial_statuses = ['PLANNING', 'REGISTRATION_OPEN']
        if value.status_code not in allowed_initial_statuses:
            raise serializers.ValidationError(
                f"创建赛事时状态必须是: {', '.join(allowed_initial_statuses)}"
            )
        return value


class TournamentStatusUpdateSerializer(serializers.Serializer):
    """赛事状态更新序列化器"""
    status_id = serializers.UUIDField(required=True)

    def validate_status_id(self, value):
        """验证状态ID"""
        try:
            status = DjangoTournamentStatus.objects.get(pk=value)
            return value
        except DjangoTournamentStatus.DoesNotExist:
            raise serializers.ValidationError("指定的状态不存在")
