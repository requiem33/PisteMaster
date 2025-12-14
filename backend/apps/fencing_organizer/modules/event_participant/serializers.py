from rest_framework import serializers
from django.core.validators import MinValueValidator
from .models import DjangoEventParticipant
from ..event.models import DjangoEvent
from ..fencer.models import DjangoFencer


class EventParticipantSerializer(serializers.ModelSerializer):
    """EventParticipant API序列化器"""

    # 嵌套序列化器字段（写操作）
    event = serializers.PrimaryKeyRelatedField(
        queryset=DjangoEvent.objects.all(),
        write_only=True,
        required=True
    )
    fencer = serializers.PrimaryKeyRelatedField(
        queryset=DjangoFencer.objects.all(),
        write_only=True,
        required=True
    )

    # 只读嵌套字段（用于输出）
    event_info = serializers.SerializerMethodField(read_only=True)
    fencer_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DjangoEventParticipant
        fields = [
            'id',
            'event',
            'fencer',
            'event_info',
            'fencer_info',
            'seed_rank',
            'seed_value',
            'is_confirmed',
            'registration_time',
            'notes',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'registration_time']

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

    def get_fencer_info(self, obj):
        """获取运动员信息"""
        if obj.fencer:
            return {
                'id': str(obj.fencer.id),
                'first_name': obj.fencer.first_name,
                'last_name': obj.fencer.last_name,
                'display_name': obj.fencer.display_name,
                'country_code': obj.fencer.country_code,
                'primary_weapon': obj.fencer.primary_weapon
            }
        return None

    def validate(self, data):
        """整体验证"""
        errors = {}

        # 验证种子排名
        if 'seed_rank' in data and data['seed_rank'] is not None:
            if data['seed_rank'] < 1:
                errors['seed_rank'] = "种子排名必须大于0"

        # 验证种子分值
        if 'seed_value' in data and data['seed_value'] is not None:
            if data['seed_value'] < 0:
                errors['seed_value'] = "种子分值不能为负数"

        if errors:
            raise serializers.ValidationError(errors)

        return data


class EventParticipantCreateSerializer(EventParticipantSerializer):
    """创建EventParticipant序列化器"""

    class Meta(EventParticipantSerializer.Meta):
        fields = EventParticipantSerializer.Meta.fields

    def create(self, validated_data):
        """创建EventParticipant"""
        # 确保同一个运动员在同一个事件中只能有一个记录
        event = validated_data['event']
        fencer = validated_data['fencer']

        if DjangoEventParticipant.objects.filter(event=event, fencer=fencer).exists():
            raise serializers.ValidationError({
                'fencer': '该运动员已在此事件中注册'
            })

        return super().create(validated_data)


class EventParticipantUpdateSerializer(EventParticipantSerializer):
    """更新EventParticipant序列化器"""

    class Meta(EventParticipantSerializer.Meta):
        fields = EventParticipantSerializer.Meta.fields

    def validate(self, data):
        """更新时的验证"""
        validated_data = super().validate(data)

        # 不允许更新event和fencer
        if 'event' in validated_data or 'fencer' in validated_data:
            raise serializers.ValidationError("不能修改事件或运动员")

        return validated_data


class EventParticipantBulkRegisterSerializer(serializers.Serializer):
    """批量注册序列化器"""
    fencer_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1
    )


class EventParticipantSeedUpdateSerializer(serializers.Serializer):
    """种子排名更新序列化器"""
    fencer_id = serializers.UUIDField(required=True)
    seed_rank = serializers.IntegerField(
        required=True,
        validators=[MinValueValidator(1)]
    )
    seed_value = serializers.FloatField(
        required=False,
        allow_null=True
    )
