from rest_framework import serializers

from backend.apps.cluster.serializers.base import DomainModelSerializer
from backend.apps.cluster.models import DjangoSyncLog


class SyncLogSerializer(DomainModelSerializer):
    """Serializer for SyncLog - handles both Django ORM and domain models."""

    id = serializers.IntegerField(read_only=True)
    table_name = serializers.CharField(max_length=100, required=True)
    record_id = serializers.CharField(max_length=100, required=True)
    operation = serializers.CharField(max_length=10, required=True)
    data = serializers.JSONField(required=True)
    version = serializers.IntegerField(required=False, default=1)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = DjangoSyncLog
        fields = [
            "id",
            "table_name",
            "record_id",
            "operation",
            "data",
            "version",
            "created_at",
        ]

    def validate_operation(self, value):
        valid_operations = ["INSERT", "UPDATE", "DELETE"]
        if value not in valid_operations:
            raise serializers.ValidationError(f"Invalid operation: {value}. Must be one of {valid_operations}")
        return value

    def validate_table_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Table name cannot be empty")
        return value.strip()

    def validate_record_id(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Record ID cannot be empty")
        return value.strip()


class SyncLogCreateSerializer(DomainModelSerializer):
    """Serializer for creating SyncLog entries."""

    table_name = serializers.CharField(max_length=100, required=True)
    record_id = serializers.CharField(max_length=100, required=True)
    operation = serializers.CharField(max_length=10, required=True)
    data = serializers.JSONField(required=True)
    version = serializers.IntegerField(required=False, default=1)

    class Meta:
        model = DjangoSyncLog
        fields = ["table_name", "record_id", "operation", "data", "version"]

    def validate_operation(self, value):
        valid_operations = ["INSERT", "UPDATE", "DELETE"]
        if value not in valid_operations:
            raise serializers.ValidationError(f"Invalid operation: {value}. Must be one of {valid_operations}")
        return value

    def validate_table_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Table name cannot be empty")
        return value.strip()

    def validate_record_id(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Record ID cannot be empty")
        return value.strip()
