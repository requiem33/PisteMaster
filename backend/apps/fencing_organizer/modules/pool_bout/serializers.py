from rest_framework import serializers
from django.core.validators import MinValueValidator
from .models import DjangoPoolBout
from ..pool.models import DjangoPool
from ..fencer.models import DjangoFencer
from ..match_status.models import DjangoMatchStatusType


class PoolBoutSerializer(serializers.ModelSerializer):
    """小组赛单场比赛序列化器"""

    # 嵌套序列化器字段（写操作）
    pool = serializers.PrimaryKeyRelatedField(
        queryset=DjangoPool.objects.all(),
        write_only=True,
        required=True
    )
    fencer_a = serializers.PrimaryKeyRelatedField(
        queryset=DjangoFencer.objects.all(),
        write_only=True,
        required=True
    )
    fencer_b = serializers.PrimaryKeyRelatedField(
        queryset=DjangoFencer.objects.all(),
        write_only=True,
        required=True
    )
    status = serializers.PrimaryKeyRelatedField(
        queryset=DjangoMatchStatusType.objects.all(),
        write_only=True,
        required=True
    )
    winner = serializers.PrimaryKeyRelatedField(
        queryset=DjangoFencer.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    # 只读嵌套字段（用于输出）
    pool_info = serializers.SerializerMethodField(read_only=True)
    fencer_a_info = serializers.SerializerMethodField(read_only=True)
    fencer_b_info = serializers.SerializerMethodField(read_only=True)
    status_info = serializers.SerializerMethodField(read_only=True)
    winner_info = serializers.SerializerMethodField(read_only=True)

    # 计算字段
    is_completed = serializers.BooleanField(read_only=True)
    is_draw = serializers.BooleanField(read_only=True)
    is_forfeited = serializers.BooleanField(read_only=True)
    is_ready_to_start = serializers.BooleanField(read_only=True)
    target_score = serializers.IntegerField(read_only=True)
    is_score_valid = serializers.BooleanField(read_only=True)
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = DjangoPoolBout
        fields = [
            'id',
            'pool',
            'fencer_a',
            'fencer_b',
            'status',
            'winner',
            'pool_info',
            'fencer_a_info',
            'fencer_b_info',
            'status_info',
            'winner_info',
            'fencer_a_score',
            'fencer_b_score',
            'scheduled_time',
            'actual_start_time',
            'actual_end_time',
            'duration_seconds',
            'notes',
            'is_completed',
            'is_draw',
            'is_forfeited',
            'is_ready_to_start',
            'target_score',
            'is_score_valid',
            'display_name',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_pool_info(self, obj):
        """获取小组信息"""
        if obj.pool:
            return {
                'id': str(obj.pool.id),
                'pool_number': obj.pool.pool_number,
                'pool_letter': obj.pool.pool_letter,
                'event_name': obj.pool.event.event_name if obj.pool.event else None
            }
        return None

    def get_fencer_a_info(self, obj):
        """获取运动员A信息"""
        if obj.fencer_a:
            return {
                'id': str(obj.fencer_a.id),
                'first_name': obj.fencer_a.first_name,
                'last_name': obj.fencer_a.last_name,
                'display_name': obj.fencer_a.display_name,
                'country_code': obj.fencer_a.country_code
            }
        return None

    def get_fencer_b_info(self, obj):
        """获取运动员B信息"""
        if obj.fencer_b:
            return {
                'id': str(obj.fencer_b.id),
                'first_name': obj.fencer_b.first_name,
                'last_name': obj.fencer_b.last_name,
                'display_name': obj.fencer_b.display_name,
                'country_code': obj.fencer_b.country_code
            }
        return None

    def get_status_info(self, obj):
        """获取状态信息"""
        if obj.status:
            return {
                'id': str(obj.status.id),
                'status_code': obj.status.status_code,
                'description': obj.status.description
            }
        return None

    def get_winner_info(self, obj):
        """获取胜者信息"""
        if obj.winner:
            return {
                'id': str(obj.winner.id),
                'first_name': obj.winner.first_name,
                'last_name': obj.winner.last_name,
                'display_name': obj.winner.display_name,
                'country_code': obj.winner.country_code
            }
        return None

    def validate(self, data):
        """整体验证"""
        errors = {}

        # 验证运动员不能相同
        if 'fencer_a' in data and 'fencer_b' in data:
            if data['fencer_a'] == data['fencer_b']:
                errors['fencer_b'] = "运动员A和运动员B不能是同一人"

        # 验证比分
        if 'fencer_a_score' in data and 'fencer_b_score' in data:
            if data['fencer_a_score'] < 0 or data['fencer_b_score'] < 0:
                errors['fencer_a_score'] = "比分不能为负数"
                errors['fencer_b_score'] = "比分不能为负数"

            # 如果比赛已完成，验证胜者
            if 'status' in data:
                status = data['status']
                if status.status_code == 'COMPLETED':
                    if 'winner' not in data or data['winner'] is None:
                        # 检查是否为平局
                        if data['fencer_a_score'] != data['fencer_b_score']:
                            errors['winner'] = "比赛已完成且有胜负，必须指定胜者"
                    elif data['winner'] not in [data.get('fencer_a'), data.get('fencer_b')]:
                        errors['winner'] = "胜者必须是比赛双方之一"

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        """创建比赛"""
        # 确保fencer_a_id < fencer_b_id（以满足唯一性约束）
        fencer_a = validated_data['fencer_a']
        fencer_b = validated_data['fencer_b']

        if fencer_a.id > fencer_b.id:
            # 交换运动员
            validated_data['fencer_a'], validated_data['fencer_b'] = fencer_b, fencer_a
            # 如果有比分，也需要交换
            if 'fencer_a_score' in validated_data and 'fencer_b_score' in validated_data:
                validated_data['fencer_a_score'], validated_data['fencer_b_score'] = \
                    validated_data['fencer_b_score'], validated_data['fencer_a_score']

        return super().create(validated_data)


class PoolBoutResultSerializer(serializers.Serializer):
    """比赛结果序列化器"""
    fencer_a_score = serializers.IntegerField(
        required=True,
        validators=[MinValueValidator(0)]
    )
    fencer_b_score = serializers.IntegerField(
        required=True,
        validators=[MinValueValidator(0)]
    )
    winner_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class PoolBoutStartSerializer(serializers.Serializer):
    """开始比赛序列化器"""
    actual_start_time = serializers.DateTimeField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class PoolBoutGenerateSerializer(serializers.Serializer):
    """生成比赛序列化器"""
    pool_id = serializers.UUIDField(required=True)
