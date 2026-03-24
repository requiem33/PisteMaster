from datetime import datetime
from typing import List, Optional
from uuid import UUID

from django.db import IntegrityError

from backend.apps.fencing_organizer.repositories.fencer_repo import DjangoFencerRepository
from core.models.fencer import Fencer


class FencerService:
    """
    Fencer business service.

    Validation is handled by Serializers.
    This service handles business logic only.
    """

    def __init__(self, repository: Optional[DjangoFencerRepository] = None):
        self.repository = repository or DjangoFencerRepository()

    def get_fencer_by_id(self, fencer_id: UUID) -> Optional[Fencer]:
        """Get fencer by ID."""
        return self.repository.get_fencer_by_id(fencer_id)

    def get_fencer_by_fencing_id(self, fencing_id: str) -> Optional[Fencer]:
        """Get fencer by fencing ID."""
        return self.repository.get_fencer_by_fencing_id(fencing_id)

    def get_all_fencers(self) -> List[Fencer]:
        """Get all fencers."""
        return self.repository.get_all_fencers()

    def create_fencer(self, fencer_data: dict) -> Fencer:
        """
        Create fencer.

        Validation is done by Serializer.
        This method creates the domain entity and saves it.
        """
        fencer = Fencer(
            first_name=fencer_data["first_name"],
            last_name=fencer_data["last_name"],
            display_name=fencer_data.get("display_name") or f"{fencer_data['last_name']} {fencer_data['first_name']}",
            gender=fencer_data.get("gender"),
            country_code=fencer_data.get("country_code"),
            birth_date=fencer_data.get("birth_date"),
            fencing_id=fencer_data.get("fencing_id"),
            current_ranking=fencer_data.get("current_ranking"),
            primary_weapon=fencer_data.get("primary_weapon"),
        )

        try:
            return self.repository.save_fencer(fencer)
        except IntegrityError as e:
            if "unique" in str(e).lower() and "fencing_id" in str(e):
                raise self.FencerServiceError(f"Fencing ID '{fencer_data.get('fencing_id')}' already exists")
            raise self.FencerServiceError(f"Create fencer failed: {str(e)}")

    def update_fencer(self, fencer_id: UUID, fencer_data: dict) -> Fencer:
        """
        Update fencer.

        Validation is done by Serializer.
        This method updates the domain entity and saves it.
        """
        existing_fencer = self.repository.get_fencer_by_id(fencer_id)
        if not existing_fencer:
            raise self.FencerServiceError(f"Fencer {fencer_id} not found")

        if "fencing_id" in fencer_data and fencer_data["fencing_id"]:
            existing_with_fencing_id = self.repository.get_fencer_by_fencing_id(fencer_data["fencing_id"])
            if existing_with_fencing_id and existing_with_fencing_id.id != fencer_id:
                raise self.FencerServiceError(f"Fencing ID '{fencer_data['fencing_id']}' is already used by another fencer")

        for key, value in fencer_data.items():
            if hasattr(existing_fencer, key):
                setattr(existing_fencer, key, value)

        if "first_name" in fencer_data or "last_name" in fencer_data:
            if not fencer_data.get("display_name"):
                existing_fencer.display_name = f"{existing_fencer.last_name} {existing_fencer.first_name}"

        existing_fencer.updated_at = datetime.now()

        try:
            return self.repository.save_fencer(existing_fencer)
        except IntegrityError as e:
            if "unique" in str(e).lower() and "fencing_id" in str(e):
                raise self.FencerServiceError(f"Fencing ID '{fencer_data.get('fencing_id')}' is already used by another fencer")
            raise self.FencerServiceError(f"Update fencer failed: {str(e)}")

    def delete_fencer(self, fencer_id: UUID) -> bool:
        """Delete fencer."""
        fencer = self.repository.get_fencer_by_id(fencer_id)
        if not fencer:
            raise self.FencerServiceError(f"Fencer {fencer_id} not found")

        return self.repository.delete_fencer(fencer_id)

    def search_fencers(self, query: str, limit: int = 50) -> List[Fencer]:
        """Search fencers."""
        if not query or len(query.strip()) < 1:
            raise self.FencerServiceError("Search query cannot be empty")

        return self.repository.search_fencers(query.strip(), limit)

    def get_fencers_by_country(self, country_code: str) -> List[Fencer]:
        """Get fencers by country."""
        if not country_code or len(country_code) != 3:
            raise self.FencerServiceError("Country code must be 3 letters")

        return self.repository.get_fencers_by_country(country_code)

    def get_fencers_by_weapon(self, weapon: str) -> List[Fencer]:
        """Get fencers by weapon."""
        valid_weapons = ["FOIL", "EPEE", "SABRE", None]
        if weapon.upper() not in valid_weapons:
            raise self.FencerServiceError(f"Weapon must be one of: {', '.join([w for w in valid_weapons if w])}")

        return self.repository.get_fencers_by_weapon(weapon.upper())

    def get_statistics(self) -> dict:
        """Get fencer statistics."""
        return self.repository.count_fencers()

    def get_top_ranked_fencers(self, limit: int = 100, country: str = None) -> List[Fencer]:
        """Get top ranked fencers."""
        return self.repository.get_top_ranked_fencers(limit, country)

    class FencerServiceError(Exception):
        """Service layer exception."""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
