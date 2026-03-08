from rest_framework import serializers
from django.core.validators import MinValueValidator
from .models import DjangoPool
from ..event.models import DjangoEvent


class PoolSerializer(serializers.ModelSerializer):
    """小组序列化器"""

    # 嵌套序列化器字段（写操作）
    event = serializers.PrimaryKeyRelatedField(
        queryset=DjangoEvent.objects.all(),
        write_only=True,
        required=True
    )

    # 只读嵌套字段（用于输出）
    event_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DjangoPool
        fields = [
            'id',
            'event',
            'stage_id',
            'event_info',
            'pool_number',
            'fencer_ids',
            'results',
            'stats',
            'is_locked',
            'start_time',
            'status',
            'is_completed',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_event_info(self, obj):
        """获取事件信息"""
        if obj.event:
            return {
                'id': str(obj.event.id),
                'event_name': obj.event.event_name,
                'tournament_id': str(obj.event.tournament.id) if obj.event.tournament else None,
            }
        return None

    def validate(self, data):
        """整体验证"""
        errors = {}

        # 验证小组编号
        if 'pool_number' in data and data['pool_number'] < 1:
            errors['pool_number'] = "小组编号必须大于0"

        # 验证状态
        if 'status' in data:
            from core.constants.pool import PoolStatus
            valid_statuses = [status.value for status in PoolStatus]
            if data['status'] not in valid_statuses:
                errors['status'] = f"状态必须是: {', '.join(valid_statuses)}"

        if errors:
            raise serializers.ValidationError(errors)

        return data


class PoolCreateSerializer(PoolSerializer):
    """创建小组序列化器"""
    pass


class PoolUpdateSerializer(PoolSerializer):
    """更新小组序列化器"""
    pass
