from rest_framework import serializers

from backend.apps.fencing_organizer.serializers.base import DomainModelSerializer
from .models import DjangoTournament


class TournamentSerializer(DomainModelSerializer):
    """
    Tournament serializer - handles both Django ORM models and domain models (dataclasses).

    Extends DomainModelSerializer for Clean Architecture compatibility.
    """

    id = serializers.UUIDField(read_only=True)
    tournament_name = serializers.CharField(max_length=200, required=True)
    organizer = serializers.CharField(max_length=200, required=False, allow_null=True)
    location = serializers.CharField(max_length=200, required=False, allow_null=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    status = serializers.CharField(max_length=20, required=False, default="PLANNING")
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = DjangoTournament
        fields = [
            "id",
            "tournament_name",
            "organizer",
            "location",
            "start_date",
            "end_date",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate_tournament_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Tournament name cannot be empty")
        if len(value) > 200:
            raise serializers.ValidationError(
                "Tournament name cannot exceed 200 characters"
            )
        return value.strip()

    def validate(self, attrs):
        if attrs.get("start_date") and attrs.get("end_date"):
            if attrs["end_date"] < attrs["start_date"]:
                raise serializers.ValidationError(
                    {"end_date": "End date cannot be earlier than start date"}
                )
        return attrs


class TournamentCreateSerializer(DomainModelSerializer):
    """
    Tournament create serializer - for creating new tournaments.
    """

    tournament_name = serializers.CharField(max_length=200, required=True)
    organizer = serializers.CharField(max_length=200, required=False, allow_null=True)
    location = serializers.CharField(max_length=200, required=False, allow_null=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    status = serializers.CharField(max_length=20, required=False, default="PLANNING")

    class Meta:
        model = DjangoTournament
        fields = [
            "tournament_name",
            "organizer",
            "location",
            "start_date",
            "end_date",
            "status",
        ]

    def validate_tournament_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Tournament name cannot be empty")
        return value.strip()

    def validate(self, attrs):
        if (
            attrs.get("end_date")
            and attrs.get("start_date")
            and attrs["end_date"] < attrs["start_date"]
        ):
            raise serializers.ValidationError(
                {"end_date": "End date cannot be earlier than start date"}
            )
        return attrs
