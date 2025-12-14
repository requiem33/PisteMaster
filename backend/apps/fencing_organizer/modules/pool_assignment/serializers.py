from rest_framework import serializers
from django.core.validators import MinValueValidator
from .models import DjangoPoolAssignment
from ..pool.models import DjangoPool
from ..fencer.models import DjangoFencer


class PoolAssignmentSerializer(serializers.ModelSerializer):
    """PoolAssignment API序列化器"""

    # 嵌套序列化器字段（写操作）
    pool = serializers.PrimaryKeyRelatedField(
        queryset=DjangoPool.objects.all(),
        write_only=True,
        required=True
    )
    fencer = serializers.PrimaryKeyRelatedField(
        queryset=DjangoFencer.objects.all(),
        write_only=True,
        required=True
    )

    # 只读嵌套字段（用于输出）
    pool_info = serializers.SerializerMethodField(read_only=True)
    fencer_info = serializers.SerializerMethodField(read_only=True)

    # 计算字段
    win_rate = serializers.FloatField(read_only=True)
    average_touches_scored = serializers.FloatField(read_only=True)
    average_touches_received = serializers.FloatField(read_only=True)

    class Meta:
        model = DjangoPoolAssignment
        fields = [
            'id',
            'pool',
            'fencer',
            'pool_info',
            'fencer_info',
            'final_pool_rank',
            'victories',
            'indicator',
            'touches_scored',
            'touches_received',
            'matches_played',
            'is_qualified',
            'qualification_rank',
            'win_rate',
            'average_touches_scored',
            'average_touches_received',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'indicator', 'created_at', 'updated_at']

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

        # 验证排名
        if 'final_pool_rank' in data and data['final_pool_rank'] is not None:
            if data['final_pool_rank'] < 1:
                errors['final_pool_rank'] = "排名必须大于0"

        # 验证比赛数据
        if 'victories' in data and data['victories'] < 0:
            errors['victories'] = "胜场数不能为负数"

        if 'touches_scored' in data and data['touches_scored'] < 0:
            errors['touches_scored'] = "得分不能为负数"

        if 'touches_received' in data and data['touches_received'] < 0:
            errors['touches_received'] = "失分不能为负数"

        if 'matches_played' in data and data['matches_played'] < 0:
            errors['matches_played'] = "已赛场次不能为负数"

        # 验证胜场数不超过已赛场次
        if ('victories' in data and 'matches_played' in data and
                data['victories'] > data['matches_played']):
            errors['victories'] = "胜场数不能超过已赛场次"

        if errors:
            raise serializers.ValidationError(errors)

        return data


class PoolAssignmentCreateSerializer(PoolAssignmentSerializer):
    """创建PoolAssignment序列化器"""

    class Meta(PoolAssignmentSerializer.Meta):
        fields = PoolAssignmentSerializer.Meta.fields

    def create(self, validated_data):
        """创建PoolAssignment"""
        # 确保同一个运动员在同一个小组中只能有一个记录
        pool = validated_data['pool']
        fencer = validated_data['fencer']

        if DjangoPoolAssignment.objects.filter(pool=pool, fencer=fencer).exists():
            raise serializers.ValidationError({
                'fencer': '该运动员已在此小组中'
            })

        return super().create(validated_data)


class PoolAssignmentUpdateSerializer(PoolAssignmentSerializer):
    """更新PoolAssignment序列化器"""

    class Meta(PoolAssignmentSerializer.Meta):
        fields = PoolAssignmentSerializer.Meta.fields

    def validate(self, data):
        """更新时的验证"""
        validated_data = super().validate(data)

        # 不允许更新pool和fencer
        if 'pool' in validated_data or 'fencer' in validated_data:
            raise serializers.ValidationError("不能修改小组或运动员")

        return validated_data


class PoolAssignmentMatchResultSerializer(serializers.Serializer):
    """比赛结果序列化器"""
    touches_scored = serializers.IntegerField(
        required=True,
        validators=[MinValueValidator(0)]
    )
    touches_received = serializers.IntegerField(
        required=True,
        validators=[MinValueValidator(0)]
    )
    is_winner = serializers.BooleanField(default=False)


class PoolAssignmentBulkCreateSerializer(serializers.Serializer):
    """批量创建序列化器"""
    fencer_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1
    )


class PoolAssignmentRankingUpdateSerializer(serializers.Serializer):
    """排名更新序列化器"""
    fencer_id = serializers.UUIDField(required=True)
    final_pool_rank = serializers.IntegerField(
        required=True,
        validators=[MinValueValidator(1)]
    )
    is_qualified = serializers.BooleanField(default=False)
    qualification_rank = serializers.IntegerField(
        required=False,
        allow_null=True,
        validators=[MinValueValidator(1)]
    )
