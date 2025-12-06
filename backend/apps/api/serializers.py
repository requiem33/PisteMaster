# backend/apps/api/serializers.py
from rest_framework import serializers
from .models import Fencer


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