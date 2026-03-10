from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from django.db import IntegrityError

from backend.apps.fencing_organizer.repositories.tournament_repo import DjangoTournamentRepository
from core.models.tournament import Tournament


class TournamentService:
    """
    Tournament business service.

    Validation is handled by Serializers.
    This service handles business logic only.
    """

    def __init__(self, repository: Optional[DjangoTournamentRepository] = None):
        self.repository = repository or DjangoTournamentRepository()

    def get_tournament_by_id(self, tournament_id: UUID) -> Optional[Tournament]:
        """Get tournament by ID."""
        return self.repository.get_tournament_by_id(tournament_id)

    def get_all_tournaments(self) -> List[Tournament]:
        """Get all tournaments."""
        return self.repository.get_all_tournaments()

    def get_upcoming_tournaments(self, days: int = 30) -> List[Tournament]:
        """Get upcoming tournaments within N days."""
        today = date.today()
        future_date = today + timedelta(days=days)

        tournaments = self.repository.get_tournaments_by_date_range(today, future_date)
        return [t for t in tournaments if t.end_date >= today]

    def get_ongoing_tournaments(self) -> List[Tournament]:
        """Get ongoing tournaments."""
        today = date.today()
        tournaments = self.repository.get_tournaments_by_date_range(today, today)
        return [t for t in tournaments if t.status == "ONGOING"]

    def create_tournament(self, tournament_data: dict) -> Tournament:
        """
        Create tournament.

        Validation is done by Serializer.
        This method creates the domain entity and saves it.
        """
        try:
            tournament_entity = Tournament(
                tournament_name=tournament_data['tournament_name'],
                start_date=tournament_data['start_date'],
                end_date=tournament_data['end_date'],
                organizer=tournament_data.get('organizer'),
                location=tournament_data.get('location'),
                status=tournament_data.get('status', 'PLANNING')
            )

            return self.repository.save_tournament(tournament_entity)

        except IntegrityError as e:
            raise self.TournamentServiceError(f"Database integrity error: {str(e)}")
        except KeyError as e:
            raise self.TournamentServiceError(f"Missing required field: {str(e)}")

    def update_tournament(self, tournament_id: UUID, tournament_data: dict) -> Tournament:
        """
        Update tournament.

        Validation is done by Serializer.
        This method updates the domain entity and saves it.
        """
        existing_tournament = self.repository.get_tournament_by_id(tournament_id)
        if not existing_tournament:
            raise self.TournamentServiceError(f"Tournament {tournament_id} not found")

        for key, value in tournament_data.items():
            if hasattr(existing_tournament, key):
                setattr(existing_tournament, key, value)

        try:
            return self.repository.save_tournament(existing_tournament)
        except IntegrityError as e:
            raise self.TournamentServiceError(f"Update failed: {str(e)}")

    def delete_tournament(self, tournament_id: UUID) -> bool:
        """Delete tournament."""
        tournament = self.repository.get_tournament_by_id(tournament_id)
        if not tournament:
            return False

        return self.repository.delete_tournament(tournament_id)

    def search_tournaments(self, **filters) -> List[Tournament]:
        """Search tournaments."""
        return self.repository.search_tournaments(**filters)

    class TournamentServiceError(Exception):
        """Service layer exception."""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
