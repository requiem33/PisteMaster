from rest_framework import serializers

from backend.apps.fencing_organizer.serializers.base import DomainModelSerializer
from .models import DjangoEvent
from ..tournament.models import DjangoTournament
from ..rule.models import DjangoRule


class EventSerializer(DomainModelSerializer):
    """
    Event serializer - handles both Django ORM models and domain models (dataclasses).

    Extends DomainModelSerializer for Clean Architecture compatibility.
    """

    id = serializers.UUIDField(read_only=True)
    event_name = serializers.CharField(max_length=200, required=True)
    tournament_id = serializers.PrimaryKeyRelatedField(
        queryset=DjangoTournament.objects.all(),
        source='tournament',
        write_only=True,
        required=True
    )
    rule_id = serializers.PrimaryKeyRelatedField(
        queryset=DjangoRule.objects.all(),
        source='rule',
        write_only=True,
        required=False,
        allow_null=True
    )
    event_type = serializers.CharField(max_length=50, required=False, default='')
    status = serializers.CharField(max_length=20, required=False, default='REGISTRATION')
    current_step = serializers.IntegerField(required=False, default=0)
    live_ranking = serializers.JSONField(required=False, default=list)
    de_trees = serializers.JSONField(required=False, default=dict)
    is_team_event = serializers.BooleanField(required=False, default=False)
    start_time = serializers.DateTimeField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    tournament_info = serializers.SerializerMethodField(read_only=True)
    rule_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DjangoEvent
        fields = [
            'id',
            'event_name',
            'tournament_id',
            'rule_id',
            'event_type',
            'status',
            'current_step',
            'live_ranking',
            'de_trees',
            'tournament_info',
            'rule_info',
            'is_team_event',
            'start_time',
            'created_at',
            'updated_at'
        ]

    def get_tournament_info(self, obj):
        if hasattr(obj, 'tournament_id'):
            tournament_id = obj.tournament_id
            try:
                tournament = DjangoTournament.objects.get(id=tournament_id)
                return {
                    'id': str(tournament.id),
                    'tournament_name': tournament.tournament_name,
                    'start_date': tournament.start_date,
                    'end_date': tournament.end_date
                }
            except DjangoTournament.DoesNotExist:
                return None
        elif hasattr(obj, 'tournament') and obj.tournament:
            return {
                'id': str(obj.tournament.id),
                'tournament_name': obj.tournament.tournament_name,
                'start_date': obj.tournament.start_date,
                'end_date': obj.tournament.end_date
            }
        return None

    def get_rule_info(self, obj):
        if hasattr(obj, 'rule_id') and obj.rule_id:
            try:
                rule = DjangoRule.objects.get(id=obj.rule_id)
                return {
                    'id': str(rule.id),
                    'rule_name': rule.rule_name,
                    'pool_size': rule.pool_size,
                    'total_qualified_count': rule.total_qualified_count
                }
            except DjangoRule.DoesNotExist:
                return None
        elif hasattr(obj, 'rule') and obj.rule:
            return {
                'id': str(obj.rule.id),
                'rule_name': obj.rule.rule_name,
                'pool_size': obj.rule.pool_size,
                'total_qualified_count': obj.rule.total_qualified_count
            }
        return None

    def validate_event_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Event name cannot be empty")
        if len(value) > 200:
            raise serializers.ValidationError("Event name cannot exceed 200 characters")
        return value.strip()


class EventCreateSerializer(DomainModelSerializer):
    """
    Event create serializer - for creating new events.
    """

    tournament_id = serializers.PrimaryKeyRelatedField(
        queryset=DjangoTournament.objects.all(),
        source='tournament',
        write_only=True,
        required=True
    )
    event_name = serializers.CharField(max_length=200, required=True)
    event_type = serializers.CharField(max_length=50, required=False, default='')
    rule_id = serializers.PrimaryKeyRelatedField(
        queryset=DjangoRule.objects.all(),
        source='rule',
        write_only=True,
        required=False,
        allow_null=True
    )
    is_team_event = serializers.BooleanField(required=False, default=False)
    status = serializers.CharField(max_length=20, required=False, default='REGISTRATION')

    class Meta:
        model = DjangoEvent
        fields = [
            'tournament_id',
            'event_name',
            'event_type',
            'rule_id',
            'is_team_event',
            'status'
        ]

    def validate_event_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Event name cannot be empty")
        return value.strip()
