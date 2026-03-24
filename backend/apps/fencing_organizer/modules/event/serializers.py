from rest_framework import serializers

from backend.apps.fencing_organizer.serializers.base import DomainModelSerializer
from .models import DjangoEvent
from ..tournament.models import DjangoTournament
from ..rule.models import DjangoRule


DEFAULT_WORLD_CUP_STAGES = [
    {"type": "pool", "config": {"byes": 16, "hits": 5, "elimination_rate": 20}},
    {"type": "de", "config": {"hits": 15, "final_stage": "bronze_medal", "rank_to": 8}},
]


class EventSerializer(DomainModelSerializer):
    """
    Event serializer - handles both Django ORM models and domain models (dataclasses).

    Extends DomainModelSerializer for Clean Architecture compatibility.

    Rule resolution priority:
    1. custom_rule_config.stages if exists
    2. rule.stages_config if rule exists
    3. Default World Cup stages
    """

    id = serializers.UUIDField(read_only=True)
    event_name = serializers.CharField(max_length=200, required=True)
    tournament_id = serializers.PrimaryKeyRelatedField(
        queryset=DjangoTournament.objects.all(),
        source="tournament",
        write_only=True,
        required=True,
    )
    rule_id = serializers.PrimaryKeyRelatedField(
        queryset=DjangoRule.objects.all(),
        source="rule",
        write_only=True,
        required=False,
        allow_null=True,
    )
    event_type = serializers.CharField(max_length=50, required=False, default="")
    status = serializers.CharField(
        max_length=20, required=False, default="REGISTRATION"
    )
    current_step = serializers.IntegerField(required=False, default=0)
    live_ranking = serializers.JSONField(required=False, default=list)
    de_trees = serializers.JSONField(required=False, default=dict)
    custom_rule_config = serializers.JSONField(required=False, default=dict)
    is_team_event = serializers.BooleanField(required=False, default=False)
    start_time = serializers.DateTimeField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    tournament_info = serializers.SerializerMethodField(read_only=True)
    rule_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DjangoEvent
        fields = [
            "id",
            "event_name",
            "tournament_id",
            "rule_id",
            "event_type",
            "status",
            "current_step",
            "live_ranking",
            "de_trees",
            "custom_rule_config",
            "tournament_info",
            "rule_info",
            "is_team_event",
            "start_time",
            "created_at",
            "updated_at",
        ]

    def get_tournament_info(self, obj):
        if hasattr(obj, "tournament_id"):
            tournament_id = obj.tournament_id
            try:
                tournament = DjangoTournament.objects.get(id=tournament_id)
                return {
                    "id": str(tournament.id),
                    "tournament_name": tournament.tournament_name,
                    "start_date": tournament.start_date,
                    "end_date": tournament.end_date,
                }
            except DjangoTournament.DoesNotExist:
                return None
        elif hasattr(obj, "tournament") and obj.tournament:
            return {
                "id": str(obj.tournament.id),
                "tournament_name": obj.tournament.tournament_name,
                "start_date": obj.tournament.start_date,
                "end_date": obj.tournament.end_date,
            }
        return None

    def get_rule_info(self, obj):
        """
        Get rule info with stages.

        Priority:
        1. custom_rule_config.stages if exists
        2. rule.stages_config if rule exists
        3. Default World Cup stages
        """
        custom_rule_config = None
        if hasattr(obj, "custom_rule_config"):
            custom_rule_config = obj.custom_rule_config
        elif hasattr(obj, "__dict__") and "custom_rule_config" in obj.__dict__:
            custom_rule_config = obj.custom_rule_config

        if custom_rule_config and isinstance(custom_rule_config, dict):
            stages = custom_rule_config.get("stages", [])
            if stages:
                return {
                    "id": None,
                    "rule_name": "Custom",
                    "is_preset": False,
                    "preset_code": "custom",
                    "stages": stages,
                    "is_custom": True,
                }

        rule = None
        rule_id = None
        if hasattr(obj, "rule_id") and obj.rule_id:
            rule_id = obj.rule_id
        elif hasattr(obj, "rule") and obj.rule:
            rule = obj.rule

        if rule_id and not rule:
            try:
                rule = DjangoRule.objects.get(id=rule_id)
            except DjangoRule.DoesNotExist:
                rule = None

        if rule:
            stages = (
                rule.stages_config if rule.stages_config else DEFAULT_WORLD_CUP_STAGES
            )
            return {
                "id": str(rule.id),
                "rule_name": rule.rule_name,
                "is_preset": rule.is_preset,
                "preset_code": rule.preset_code,
                "stages": stages,
                "is_custom": False,
                "pool_size": rule.pool_size,
                "total_qualified_count": rule.total_qualified_count,
            }

        return {
            "id": None,
            "rule_name": "World Cup (Default)",
            "is_preset": True,
            "preset_code": "world_cup",
            "stages": DEFAULT_WORLD_CUP_STAGES,
            "is_custom": False,
        }

    def validate_event_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Event name cannot be empty")
        if len(value) > 200:
            raise serializers.ValidationError("Event name cannot exceed 200 characters")
        return value.strip()

    def validate_custom_rule_config(self, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("custom_rule_config must be an object")
        if "stages" in value:
            if not isinstance(value["stages"], list):
                raise serializers.ValidationError("stages must be a list")
            for stage in value["stages"]:
                if not isinstance(stage, dict):
                    raise serializers.ValidationError("Each stage must be an object")
                if "type" not in stage:
                    raise serializers.ValidationError(
                        "Each stage must have a 'type' field"
                    )
                if stage["type"] not in ["pool", "de"]:
                    raise serializers.ValidationError(
                        "Stage type must be 'pool' or 'de'"
                    )
        return value


class EventCreateSerializer(DomainModelSerializer):
    """
    Event create serializer - for creating new events.
    """

    tournament_id = serializers.PrimaryKeyRelatedField(
        queryset=DjangoTournament.objects.all(),
        source="tournament",
        write_only=True,
        required=True,
    )
    event_name = serializers.CharField(max_length=200, required=True)
    event_type = serializers.CharField(max_length=50, required=False, default="")
    rule_id = serializers.PrimaryKeyRelatedField(
        queryset=DjangoRule.objects.all(),
        source="rule",
        write_only=True,
        required=False,
        allow_null=True,
    )
    custom_rule_config = serializers.JSONField(required=False, default=dict)
    is_team_event = serializers.BooleanField(required=False, default=False)
    status = serializers.CharField(
        max_length=20, required=False, default="REGISTRATION"
    )
    start_time = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = DjangoEvent
        fields = [
            "tournament_id",
            "event_name",
            "event_type",
            "rule_id",
            "start_time",
            "custom_rule_config",
            "is_team_event",
            "status",
        ]

    def validate_event_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Event name cannot be empty")
        return value.strip()

    def validate_custom_rule_config(self, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("custom_rule_config must be an object")
        if "stages" in value:
            if not isinstance(value["stages"], list):
                raise serializers.ValidationError("stages must be a list")
            for stage in value["stages"]:
                if not isinstance(stage, dict):
                    raise serializers.ValidationError("Each stage must be an object")
                if "type" not in stage:
                    raise serializers.ValidationError(
                        "Each stage must have a 'type' field"
                    )
                if stage["type"] not in ["pool", "de"]:
                    raise serializers.ValidationError(
                        "Stage type must be 'pool' or 'de'"
                    )
        return value
