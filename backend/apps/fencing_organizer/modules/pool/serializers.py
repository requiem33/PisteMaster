from rest_framework import serializers

from backend.apps.fencing_organizer.serializers.base import VersionedModelSerializer
from .models import DjangoPool
from ..event.models import DjangoEvent


class PoolSerializer(VersionedModelSerializer):
    """
    Pool serializer - handles both Django ORM models and domain models (dataclasses).

    Extends DomainModelSerializer for Clean Architecture compatibility.
    """

    id = serializers.UUIDField(read_only=True)
    event = serializers.PrimaryKeyRelatedField(queryset=DjangoEvent.objects.all(), write_only=True, required=True)
    stage_id = serializers.CharField(max_length=50, required=False, default="1")
    pool_number = serializers.IntegerField(required=True)
    fencer_ids = serializers.JSONField(required=False, default=list)
    results = serializers.JSONField(required=False, default=list)
    stats = serializers.JSONField(required=False, default=list)
    is_locked = serializers.BooleanField(required=False, default=False)
    status = serializers.CharField(max_length=20, required=False, default="SCHEDULED")
    is_completed = serializers.BooleanField(required=False, default=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    event_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DjangoPool
        fields = [
            "id",
            "event",
            "stage_id",
            "event_info",
            "pool_number",
            "fencer_ids",
            "results",
            "stats",
            "is_locked",
            "status",
            "is_completed",
            "created_at",
            "updated_at",
        ]

    def get_event_info(self, obj):
        if hasattr(obj, "event_id"):
            event_id = obj.event_id
            try:
                event = DjangoEvent.objects.get(id=event_id)
                return {
                    "id": str(event.id),
                    "event_name": event.event_name,
                    "tournament_id": str(event.tournament.id) if event.tournament else None,
                }
            except DjangoEvent.DoesNotExist:
                return None
        elif hasattr(obj, "event") and obj.event:
            return {
                "id": str(obj.event.id),
                "event_name": obj.event.event_name,
                "tournament_id": str(obj.event.tournament.id) if obj.event.tournament else None,
            }
        return None

    def validate_pool_number(self, value):
        if value < 1:
            raise serializers.ValidationError("Pool number must be greater than 0")
        return value

    def validate_status(self, value):
        from core.constants.pool import PoolStatus

        valid_statuses = [status.value for status in PoolStatus]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value


class PoolCreateSerializer(VersionedModelSerializer):
    """
    Pool create serializer - for creating new pools.
    """

    id = serializers.UUIDField(read_only=True)
    event = serializers.PrimaryKeyRelatedField(queryset=DjangoEvent.objects.all(), write_only=True, required=True)
    stage_id = serializers.CharField(max_length=50, required=False, default="1")
    pool_number = serializers.IntegerField(required=True)
    fencer_ids = serializers.JSONField(required=False, default=list)

    class Meta:
        model = DjangoPool
        fields = ["id", "event", "stage_id", "pool_number", "fencer_ids"]

    def validate_pool_number(self, value):
        if value < 1:
            raise serializers.ValidationError("Pool number must be greater than 0")
        return value


class PoolUpdateSerializer(VersionedModelSerializer):
    """
    Pool update serializer - for updating existing pools.
    """

    pool_number = serializers.IntegerField(required=False)
    fencer_ids = serializers.JSONField(required=False)
    results = serializers.JSONField(required=False)
    stats = serializers.JSONField(required=False)
    is_locked = serializers.BooleanField(required=False)
    status = serializers.CharField(max_length=20, required=False)
    is_completed = serializers.BooleanField(required=False)

    class Meta:
        model = DjangoPool
        fields = ["pool_number", "fencer_ids", "results", "stats", "is_locked", "status", "is_completed"]

    def validate_pool_number(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("Pool number must be greater than 0")
        return value

    def validate_status(self, value):
        if value:
            from core.constants.pool import PoolStatus

            valid_statuses = [status.value for status in PoolStatus]
            if value not in valid_statuses:
                raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value
