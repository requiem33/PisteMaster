from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from django.db import IntegrityError

from backend.apps.fencing_organizer.repositories.event_repo import DjangoEventRepository
from backend.apps.fencing_organizer.repositories.tournament_repo import (
    DjangoTournamentRepository,
)
from backend.apps.fencing_organizer.repositories.rule_repo import DjangoRuleRepository
from core.models.event import Event


class EventService:
    """
    Event business service.

    Validation is handled by Serializers.
    This service handles business logic only.
    """

    def __init__(
        self,
        event_repository: Optional[DjangoEventRepository] = None,
        tournament_repository: Optional[DjangoTournamentRepository] = None,
        rule_repository: Optional[DjangoRuleRepository] = None,
    ):

        self.event_repository = event_repository or DjangoEventRepository()
        self.tournament_repository = (
            tournament_repository or DjangoTournamentRepository()
        )
        self.rule_repository = rule_repository or DjangoRuleRepository()

    def get_event_by_id(self, event_id: UUID) -> Optional[Event]:
        """Get event by ID."""
        return self.event_repository.get_event_by_id(event_id)

    def get_all_events(self) -> List[Event]:
        """Get all events."""
        return self.event_repository.get_all_events()

    def get_events_by_tournament(self, tournament_id: UUID) -> List[Event]:
        """Get events by tournament."""
        return self.event_repository.get_events_by_tournament(tournament_id)

    def get_upcoming_events(self, days: int = 7) -> List[Event]:
        """Get upcoming events within N days."""
        now = datetime.now()
        future_date = now + timedelta(days=days)

        events = self.event_repository.get_upcoming_events(now, future_date)
        return [e for e in events if not self._is_completed_or_cancelled(e)]

    def get_active_events(self) -> List[Event]:
        """Get active events (not completed and not cancelled)."""
        all_events = self.event_repository.get_all_events()
        return [e for e in all_events if not self._is_completed_or_cancelled(e)]

    def create_event(self, event_data: dict) -> Event:
        """
        Create event.

        Validation is done by Serializer.
        This method creates the domain entity and saves it.
        """
        self._validate_foreign_keys(event_data)

        event = Event(
            tournament_id=(
                event_data["tournament"].id
                if hasattr(event_data.get("tournament"), "id")
                else event_data.get("tournament_id")
            ),
            event_name=event_data["event_name"],
            rule_id=(
                event_data.get("rule").id
                if hasattr(event_data.get("rule"), "id")
                else event_data.get("rule_id")
            ),
            event_type=event_data.get("event_type", ""),
            status=event_data.get("status", "REGISTRATION"),
            is_team_event=event_data.get("is_team_event", False),
            start_time=event_data.get("start_time"),
            live_ranking=event_data.get("live_ranking", []),
            de_trees=event_data.get("de_trees", {}),
            custom_rule_config=event_data.get("custom_rule_config", {}),
            current_step=event_data.get("current_step", 0),
        )

        try:
            return self.event_repository.save_event(event)
        except IntegrityError as e:
            raise self.EventServiceError(f"Create event failed: {str(e)}")

    def update_event(self, event_id: UUID, event_data: dict) -> Event:
        """
        Update event.

        Validation is done by Serializer.
        This method updates the domain entity and saves it.
        """
        existing_event = self.event_repository.get_event_by_id(event_id)
        if not existing_event:
            raise self.EventServiceError(f"Event {event_id} not found")

        self._validate_foreign_keys(event_data)

        for key, value in event_data.items():
            if hasattr(existing_event, key):
                setattr(existing_event, key, value)

        try:
            return self.event_repository.save_event(existing_event)
        except IntegrityError as e:
            raise self.EventServiceError(f"Update event failed: {str(e)}")

    def delete_event(self, event_id: UUID) -> bool:
        """Delete event."""
        event = self.event_repository.get_event_by_id(event_id)
        if not event:
            return False

        return self.event_repository.delete_event(event_id)

    def search_events(self, **filters) -> List[Event]:
        """Search events."""
        return self.event_repository.search_events(**filters)

    def _validate_foreign_keys(self, data: dict) -> None:
        """Validate foreign key existence."""
        tournament_id = None
        if "tournament" in data and hasattr(data["tournament"], "id"):
            tournament_id = data["tournament"].id
        elif "tournament_id" in data:
            tournament_id = data["tournament_id"]

        if tournament_id:
            tournament = self.tournament_repository.get_tournament_by_id(tournament_id)
            if not tournament:
                raise self.EventServiceError(f"Tournament {tournament_id} not found")

        rule_id = None
        if "rule" in data and hasattr(data["rule"], "id"):
            rule_id = data["rule"].id
        elif "rule_id" in data:
            rule_id = data["rule_id"]

        if rule_id:
            rule = self.rule_repository.get_rule_by_id(rule_id)
            if not rule:
                raise self.EventServiceError(f"Rule {rule_id} not found")

    def _is_completed_or_cancelled(self, event: Event) -> bool:
        """Check if event is completed or cancelled."""
        return event.status in ["COMPLETED", "CANCELLED"]

    class EventServiceError(Exception):
        """Service layer exception."""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
