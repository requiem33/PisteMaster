from rest_framework import serializers
from django.core.validators import MinLengthValidator, RegexValidator
from .models import DjangoFencer


class FencerSerializer(serializers.ModelSerializer):
    """Fencer API序列化器"""

    # 计算字段
    age = serializers.IntegerField(read_only=True)
    is_international = serializers.BooleanField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = DjangoFencer
        fields = [
            'id',
            'first_name',
            'last_name',
            'display_name',
            'full_name',
            'gender',
            'country_code',
            'birth_date',
            'fencing_id',
            'current_ranking',
            'primary_weapon',
            'age',
            'is_international',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_country_code(self, value):
        """验证国家代码"""
        if value:
            value = value.upper().strip()
            if len(value) != 3:
                raise serializers.ValidationError("国家代码必须是3个字母")
            if not value.isalpha():
                raise serializers.ValidationError("国家代码只能包含字母")
        return value

    def validate_fencing_id(self, value):
        """验证击剑ID"""
        if value:
            value = value.strip()
            if len(value) > 50:
                raise serializers.ValidationError("击剑ID长度不能超过50个字符")
        return value

    def validate_birth_date(self, value):
        """验证出生日期"""
        if value:
            from datetime import date
            if value > date.today():
                raise serializers.ValidationError("出生日期不能晚于今天")
            if value.year < 1900:
                raise serializers.ValidationError("出生日期不能早于1900年")
        return value

    def validate_current_ranking(self, value):
        """验证排名"""
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("排名不能为负数")
        return value

    def validate(self, data):
        """整体验证"""
        errors = {}

        # 验证性别
        valid_genders = ['MEN', 'WOMEN', 'MIXED', 'OPEN', None]
        if 'gender' in data and data['gender'] not in valid_genders:
            errors['gender'] = f"性别必须是: {', '.join([g for g in valid_genders if g])}"

        # 验证剑种
        valid_weapons = ['FOIL', 'EPEE', 'SABRE', None]
        if 'primary_weapon' in data and data['primary_weapon'] not in valid_weapons:
            errors['primary_weapon'] = f"剑种必须是: {', '.join([w for w in valid_weapons if w])}"

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        """创建Fencer"""
        # 自动生成display_name
        if not validated_data.get('display_name'):
            validated_data['display_name'] = f"{validated_data['last_name']} {validated_data['first_name']}"

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """更新Fencer"""
        # 自动更新display_name（如果姓名被修改）
        if ('first_name' in validated_data or 'last_name' in validated_data) and not validated_data.get('display_name'):
            first_name = validated_data.get('first_name', instance.first_name)
            last_name = validated_data.get('last_name', instance.last_name)
            validated_data['display_name'] = f"{last_name} {first_name}"

        return super().update(instance, validated_data)


class FencerCreateSerializer(FencerSerializer):
    """创建Fencer序列化器"""

    class Meta(FencerSerializer.Meta):
        fields = FencerSerializer.Meta.fields


class FencerUpdateSerializer(FencerSerializer):
    """更新Fencer序列化器"""

    class Meta(FencerSerializer.Meta):
        fields = FencerSerializer.Meta.fields


class FencerSearchSerializer(serializers.Serializer):
    """搜索Fencer序列化器"""
    query = serializers.CharField(
        required=True,
        min_length=1,
        max_length=100,
        help_text="搜索词（姓名、击剑ID、国家代码）"
    )
    limit = serializers.IntegerField(
        required=False,
        default=50,
        min_value=1,
        max_value=1000,
        help_text="返回结果数量限制"
    )
