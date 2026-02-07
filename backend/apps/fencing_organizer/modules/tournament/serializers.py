from rest_framework import serializers
from django.core.validators import MinLengthValidator
from .models import DjangoTournament
from ..tournament_status.models import DjangoTournamentStatus


class TournamentSerializer(serializers.ModelSerializer):
    """赛事序列化器"""

    # 自定义字段
    status_display = serializers.CharField(source='status.display_name', read_only=True)
    status_code = serializers.CharField(source='status.status_code', read_only=True)

    class Meta:
        model = DjangoTournament
        fields = [
            'id',
            'tournament_name',
            'organizer',
            'location',
            'start_date',
            'end_date',
            'status',
            'status_display',
            'status_code',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status_display']

    def validate_tournament_name(self, value):
        """验证赛事名称"""
        if len(value.strip()) == 0:
            raise serializers.ValidationError("赛事名称不能为空")

        if len(value) > 200:
            raise serializers.ValidationError("赛事名称长度不能超过200个字符")

        return value.strip()

    def validate_start_date(self, value):
        """验证开始日期"""
        # 可以添加业务规则，比如不能是过去日期等
        return value

    def validate_end_date(self, value):
        """验证结束日期"""
        # 验证将在validate方法中进行
        return value

    def validate(self, data):
        """整体验证"""
        errors = {}

        # 检查日期顺序
        if data.get('start_date') and data.get('end_date'):
            if data['end_date'] < data['start_date']:
                errors['end_date'] = "结束日期不能早于开始日期"

        # 检查状态是否存在（如果提供了）
        if 'status' in data:
            try:
                status = DjangoTournamentStatus.objects.get(pk=data['status'])
            except DjangoTournamentStatus.DoesNotExist:
                errors['status'] = "指定的状态不存在"

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def to_internal_value(self, data):
        """处理输入数据"""
        # 将status_id转换为status（外键对象）
        if 'status_id' in data:
            data['status'] = data.pop('status_id')

        return super().to_internal_value(data)

    def to_representation(self, instance):
        """处理输出数据"""
        representation = super().to_representation(instance)

        # 添加额外的统计信息
        representation['event_count'] = getattr(instance, 'event_count', 0)

        return representation


class TournamentCreateSerializer(serializers.ModelSerializer):
    """赛事创建序列化器"""

    # 【核心修改】我们让前端直接传入 status_id
    class Meta:
        model = DjangoTournament
        fields = [
            'tournament_name',
            'organizer',
            'location',
            'start_date',
            'end_date',
        ]

    def validate(self, data):
        if data['end_date'] < data['start_date']:
            raise serializers.ValidationError({"end_date": "结束日期不能早于开始日期"})
        return data
