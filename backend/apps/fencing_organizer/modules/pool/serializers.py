from rest_framework import serializers
from django.core.validators import MinValueValidator
from .models import DjangoPool
from ..event.models import DjangoEvent
from ..piste.models import DjangoPiste


class PoolSerializer(serializers.ModelSerializer):
    """小组序列化器"""

    # 嵌套序列化器字段（写操作）
    event = serializers.PrimaryKeyRelatedField(
        queryset=DjangoEvent.objects.all(),
        write_only=True,
        required=True
    )
    piste = serializers.PrimaryKeyRelatedField(
        queryset=DjangoPiste.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    # 只读嵌套字段（用于输出）
    event_info = serializers.SerializerMethodField(read_only=True)
    piste_info = serializers.SerializerMethodField(read_only=True)

    # 计算字段
    is_active = serializers.BooleanField(read_only=True)
    participant_count = serializers.IntegerField(read_only=True)
    bout_count = serializers.IntegerField(read_only=True)
    completed_bout_count = serializers.IntegerField(read_only=True)
    completion_percentage = serializers.FloatField(read_only=True)
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = DjangoPool
        fields = [
            'id',
            'event',
            'piste',
            'event_info',
            'piste_info',
            'pool_number',
            'pool_letter',
            'start_time',
            'status',
            'is_completed',
            'is_active',
            'participant_count',
            'bout_count',
            'completed_bout_count',
            'completion_percentage',
            'display_name',
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
                'tournament_name': obj.event.tournament.tournament_name if obj.event.tournament else None
            }
        return None

    def get_piste_info(self, obj):
        """获取剑道信息"""
        if obj.piste:
            return {
                'id': str(obj.piste.id),
                'piste_number': obj.piste.piste_number,
                'location': obj.piste.location,
                'piste_type': obj.piste.piste_type,
                'is_available': obj.piste.is_available
            }
        return None

    def validate(self, data):
        """整体验证"""
        errors = {}

        # 验证小组编号
        if 'pool_number' in data and data['pool_number'] < 1:
            errors['pool_number'] = "小组编号必须大于0"

        # 验证小组字母
        if 'pool_letter' in data and data['pool_letter']:
            if len(data['pool_letter']) > 1:
                errors['pool_letter'] = "小组字母长度不能超过1个字符"
            elif not data['pool_letter'].isalpha():
                errors['pool_letter'] = "小组字母必须是英文字母"

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

    class Meta(PoolSerializer.Meta):
        fields = PoolSerializer.Meta.fields

    def validate(self, data):
        """创建时的额外验证"""
        validated_data = super().validate(data)

        # 验证小组编号是否已存在
        event = validated_data.get('event')
        pool_number = validated_data.get('pool_number')

        if event and pool_number:
            if DjangoPool.objects.filter(event=event, pool_number=pool_number).exists():
                raise serializers.ValidationError({
                    'pool_number': f"小组编号 {pool_number} 在该事件中已存在"
                })

        return validated_data


class PoolUpdateSerializer(PoolSerializer):
    """更新小组序列化器"""

    class Meta(PoolSerializer.Meta):
        fields = PoolSerializer.Meta.fields

    def validate(self, data):
        """更新时的额外验证"""
        validated_data = super().validate(data)

        # 获取实例
        instance = self.instance

        # 验证小组编号是否重复
        if 'pool_number' in validated_data and instance:
            if DjangoPool.objects.filter(
                    event=instance.event,
                    pool_number=validated_data['pool_number']
            ).exclude(id=instance.id).exists():
                raise serializers.ValidationError({
                    'pool_number': f"小组编号 {validated_data['pool_number']} 在该事件中已存在"
                })

        return validated_data


class PoolGenerateSerializer(serializers.Serializer):
    """生成小组序列化器"""
    event_id = serializers.UUIDField(required=True)
    pool_count = serializers.IntegerField(
        required=True,
        validators=[MinValueValidator(1)]
    )
    piste_id = serializers.UUIDField(required=False, allow_null=True)
