from rest_framework import serializers
from .models import DjangoFencer


class FencerSerializer(serializers.ModelSerializer):
    """Fencer模型的序列化器"""

    class Meta:
        model = DjangoFencer
        fields = '__all__'  # 包含所有字段
        read_only_fields = ['id', 'created_at', 'updated_at']  # 只读字段

    def validate_fencing_id(self, value):
        """验证fencing_id的唯一性"""
        if DjangoFencer.objects.filter(fencing_id=value).exists():
            raise serializers.ValidationError("该击剑ID已存在")
        return value

    def validate_primary_weapon(self, value):
        """验证主武器类型"""
        valid_weapons = ['Foil', 'Épée', 'Sabre']
        if value and value not in valid_weapons:
            raise serializers.ValidationError(f"无效的主武器类型，有效值为：{', '.join(valid_weapons)}")
        return value

    def validate_gender(self, value):
        """验证性别"""
        if value and value not in ['Male', 'Female', 'Other']:
            raise serializers.ValidationError(f"无效的性别，有效值为：Male, Female, Other")
        return value
