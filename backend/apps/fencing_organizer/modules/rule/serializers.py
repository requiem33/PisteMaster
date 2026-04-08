from decimal import Decimal

from rest_framework import serializers

from backend.apps.fencing_organizer.serializers.base import VersionedModelSerializer
from backend.apps.fencing_organizer.modules.elimination_type.models import DjangoEliminationType
from backend.apps.fencing_organizer.modules.ranking_type.models import DjangoRankingType
from .models import DjangoRule


class EliminationTypeSerializer(VersionedModelSerializer):
    """淘汰赛类型序列化器"""

    class Meta:
        model = DjangoEliminationType
        fields = "__all__"


class RankingTypeSerializer(VersionedModelSerializer):
    """排名类型序列化器"""

    class Meta:
        model = DjangoRankingType
        fields = "__all__"


class RuleSerializer(VersionedModelSerializer):
    """
    Rule serializer - handles both Django ORM models and domain models (dataclasses).

    Extends DomainModelSerializer for Clean Architecture compatibility.
    Returns only preset rules (is_preset=True) for the list endpoint.
    """

    id = serializers.UUIDField(read_only=True)
    rule_name = serializers.CharField(max_length=100, required=True)
    stages_config = serializers.JSONField(required=False, default=list)
    is_preset = serializers.BooleanField(read_only=True)
    preset_code = serializers.CharField(max_length=50, read_only=True)

    elimination_type = EliminationTypeSerializer(read_only=True)
    final_ranking_type = RankingTypeSerializer(read_only=True)
    elimination_type_code = serializers.CharField(source="elimination_type.type_code", read_only=True)
    ranking_type_code = serializers.CharField(source="final_ranking_type.type_code", read_only=True)

    pool_size = serializers.IntegerField(required=False, allow_null=True)
    total_qualified_count = serializers.IntegerField(required=True)
    match_score_pool = serializers.IntegerField(required=False, allow_null=True)
    match_score_elimination = serializers.IntegerField(required=False, allow_null=True)
    match_duration = serializers.IntegerField(required=False, allow_null=True)
    group_qualification_ratio = serializers.DecimalField(max_digits=5, decimal_places=4, required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = DjangoRule
        fields = [
            "id",
            "rule_name",
            "stages_config",
            "is_preset",
            "preset_code",
            "elimination_type",
            "final_ranking_type",
            "elimination_type_code",
            "ranking_type_code",
            "pool_size",
            "total_qualified_count",
            "match_score_pool",
            "match_score_elimination",
            "match_duration",
            "group_qualification_ratio",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_preset", "preset_code", "created_at", "updated_at"]

    def validate_rule_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Rule name cannot be empty")
        if len(value) > 100:
            raise serializers.ValidationError("Rule name cannot exceed 100 characters")
        return value.strip()

    def validate_pool_size(self, value):
        if value is not None and value < 3:
            raise serializers.ValidationError("Pool size must be at least 3")
        return value

    def validate_total_qualified_count(self, value):
        if value < 1:
            raise serializers.ValidationError("Total qualified count must be greater than 0")
        return value

    def validate_group_qualification_ratio(self, value):
        if value is not None:
            try:
                ratio = Decimal(str(value))
                if ratio < 0 or ratio > 1:
                    raise serializers.ValidationError("Qualification ratio must be between 0 and 1")
            except (ValueError, TypeError):
                raise serializers.ValidationError("Qualification ratio must be a valid decimal")
        return value

    def validate_stages_config(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("stages_config must be a list")
        for stage in value:
            if not isinstance(stage, dict):
                raise serializers.ValidationError("Each stage must be an object")
            if "type" not in stage:
                raise serializers.ValidationError("Each stage must have a 'type' field")
            if stage["type"] not in ["pool", "de"]:
                raise serializers.ValidationError("Stage type must be 'pool' or 'de'")
        return value


class RuleCreateSerializer(VersionedModelSerializer):
    """
    Rule create serializer - for creating new rules.
    Note: Only admins can create non-preset rules.
    """

    id = serializers.UUIDField(read_only=True)
    rule_name = serializers.CharField(max_length=100, required=True)
    elimination_type_id = serializers.UUIDField(write_only=True, required=True)
    final_ranking_type_id = serializers.UUIDField(write_only=True, required=True)
    total_qualified_count = serializers.IntegerField(required=True)
    stages_config = serializers.JSONField(required=False, default=list)
    pool_size = serializers.IntegerField(required=False, allow_null=True)
    match_score_pool = serializers.IntegerField(required=False, allow_null=True)
    match_score_elimination = serializers.IntegerField(required=False, allow_null=True)
    match_duration = serializers.IntegerField(required=False, allow_null=True)
    group_qualification_ratio = serializers.DecimalField(max_digits=5, decimal_places=4, required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = DjangoRule
        fields = [
            "id",
            "rule_name",
            "elimination_type_id",
            "final_ranking_type_id",
            "total_qualified_count",
            "stages_config",
            "pool_size",
            "match_score_pool",
            "match_score_elimination",
            "match_duration",
            "group_qualification_ratio",
            "description",
        ]

    def validate_rule_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Rule name cannot be empty")
        return value.strip()

    def validate(self, data):
        try:
            data["elimination_type"] = DjangoEliminationType.objects.get(pk=data.pop("elimination_type_id"))
        except DjangoEliminationType.DoesNotExist:
            raise serializers.ValidationError({"elimination_type_id": "Elimination type not found"})

        try:
            data["final_ranking_type"] = DjangoRankingType.objects.get(pk=data.pop("final_ranking_type_id"))
        except DjangoRankingType.DoesNotExist:
            raise serializers.ValidationError({"final_ranking_type_id": "Ranking type not found"})

        return data
