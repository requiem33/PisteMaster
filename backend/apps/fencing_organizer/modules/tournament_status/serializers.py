from rest_framework import serializers
from .models import DjangoTournamentStatus


class TournamentStatusSerializer(serializers.ModelSerializer):
    """赛事状态序列化器"""

    class Meta:
        model = DjangoTournamentStatus
        fields = ['id', 'status_code', 'display_name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_status_code(self, value):
        """验证状态代码"""
        # 检查是否已存在（更新时排除自己）
        instance = self.instance
        if instance and instance.status_code == value:
            return value

        if DjangoTournamentStatus.objects.filter(status_code=value).exists():
            raise serializers.ValidationError(f"状态代码 '{value}' 已存在")

        if len(value) > 20:
            raise serializers.ValidationError("状态代码长度不能超过20个字符")

        return value

    def validate_display_name(self, value):
        """验证显示名称"""
        if value and len(value) > 50:
            raise serializers.ValidationError("显示名称长度不能超过50个字符")
        return value

    def validate_description(self, value):
        """验证描述"""
        if value and len(value) > 200:
            raise serializers.ValidationError("描述长度不能超过200个字符")
        return value
