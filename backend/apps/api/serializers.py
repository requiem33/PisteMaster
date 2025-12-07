# backend/apps/api/serializers.py
from rest_framework import serializers
from .models import Fencer, CompetitionItem, Match
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


class FencerSerializer(serializers.ModelSerializer):
    """
    用于 Fencer 模型的序列化器。
    负责将模型实例与 JSON 数据相互转换。
    """

    # 【可选】自定义只读字段：计算年龄并暴露给 API（无需存储到数据库）
    age = serializers.IntegerField(read_only=True, help_text='根据出生日期计算的年龄')

    # 【可选】自定义只读字段：显示武器类型的中文名称
    weapon_display = serializers.CharField(
        source='get_weapon_display',
        read_only=True,
        help_text='武器类型（中文显示）'
    )

    # 【可选】自定义只读字段：显示状态的中文名称
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True,
        help_text='运动员状态（中文显示）'
    )

    class Meta:
        model = Fencer
        # 指定需要包含在 API 中的字段
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',  # 使用模型中定义的 @property
            'country',
            'region',
            'club',
            'date_of_birth',
            'gender',
            'age',  # 自定义字段
            'weapon',
            'weapon_display',  # 自定义字段
            'rating',
            'seed',
            'status',
            'status_display',  # 自定义字段
            'created_at',
            'updated_at',
        ]
        # 设置只读字段（这些字段将由系统自动处理，不允许通过API修改）
        read_only_fields = ('id', 'created_at', 'updated_at', 'age')

        # 【可选】添加字段级别的额外验证或说明
        extra_kwargs = {
            'first_name': {
                'help_text': '运动员的名',
                'min_length': 1,
                'max_length': 50,
            },
            'last_name': {
                'help_text': '运动员的姓',
                'min_length': 1,
                'max_length': 50,
            },
            'country': {
                'help_text': '国家/地区代码，建议使用3字母代码 (如 CHN)',
                'min_length': 2,
                'max_length': 3,
            },
            'rating': {
                'help_text': '运动员的积分，必须为非负数',
                'min_value': 0,
            }
        }

    # 【可选】自定义验证逻辑示例：确保姓和名不全是空格
    def validate(self, data):
        """
        对象级别的自定义验证。
        """
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        if not first_name.strip() or not last_name.strip():
            raise serializers.ValidationError({
                "name": "姓和名不能为空或仅包含空格。"
            })
        return data

    # 【可选】自定义创建或更新逻辑
    def create(self, validated_data):
        """
        创建 Fencer 实例时可以在此添加自定义逻辑。
        例如，为新选手设置默认积分。
        """
        # 调用父类方法创建实例
        instance = super().create(validated_data)
        # 你可以在这里添加额外操作，例如：发送欢迎邮件、记录日志等
        # instance.set_default_rating()
        return instance

    def update(self, instance, validated_data):
        """
        更新 Fencer 实例时可以在此添加自定义逻辑。
        """
        # 调用父类方法更新实例
        updated_instance = super().update(instance, validated_data)
        # 你可以在这里添加额外操作
        return updated_instance


class CompetitionItemSerializer(serializers.ModelSerializer):
    """比赛单项序列化器 - 基础版本"""

    # 只读字段
    rules_name = serializers.CharField(source='rules.name', read_only=True)
    participant_count = serializers.IntegerField(source='current_participants', read_only=True)

    class Meta:
        model = CompetitionItem
        fields = [
            'id',
            'name',
            'weapon_type',
            'gender_category',
            'age_group',
            'status',
            'rules',
            'rules_name',
            'max_participants',
            'participant_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'participant_count')


class MatchSerializer(serializers.ModelSerializer):
    """比赛对阵序列化器 - 基础版本"""

    # 嵌套字段
    fencer_a_info = serializers.SerializerMethodField()
    fencer_b_info = serializers.SerializerMethodField()
    competition_item_name = serializers.CharField(
        source='competition_item.name',
        read_only=True
    )

    class Meta:
        model = Match
        fields = [
            'id',
            'competition_item',
            'competition_item_name',
            'match_type',
            'status',
            'fencer_a',
            'fencer_b',
            'fencer_a_info',
            'fencer_b_info',
            'score_a',
            'score_b',
            'pool_number',
            'pool_round',
            'bracket_position',
            'round_number',
            'is_bronze_match',
            'scheduled_time',
            'piste_number',
            'started_at',
            'ended_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_fencer_a_info(self, obj):
        """获取选手A的详细信息"""
        if not obj.fencer_a:
            return {"id": -1, "name": "轮空"}
        return {
            "id": obj.fencer_a.id,
            "name": obj.fencer_a.full_name,
            "country": obj.fencer_a.country
        }

    def get_fencer_b_info(self, obj):
        """获取选手B的详细信息"""
        if not obj.fencer_b:
            return {"id": -1, "name": "轮空"}
        return {
            "id": obj.fencer_b.id,
            "name": obj.fencer_b.full_name,
            "country": obj.fencer_b.country
        }
