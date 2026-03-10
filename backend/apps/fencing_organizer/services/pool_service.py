from typing import List, Optional
from uuid import UUID

from django.db import IntegrityError

from backend.apps.fencing_organizer.repositories.pool_repo import DjangoPoolRepository
from backend.apps.fencing_organizer.repositories.event_repo import DjangoEventRepository
from backend.apps.fencing_organizer.repositories.piste_repo import DjangoPisteRepository
from core.models.pool import Pool
from core.constants.pool import PoolStatus, STATUS_TRANSITIONS


class PoolService:
    """
    Pool business service.

    Validation is handled by Serializers.
    This service handles business logic only.
    """

    def __init__(self,
                 pool_repository: Optional[DjangoPoolRepository] = None,
                 event_repository: Optional[DjangoEventRepository] = None,
                 piste_repository: Optional[DjangoPisteRepository] = None):

        self.pool_repository = pool_repository or DjangoPoolRepository()
        self.event_repository = event_repository or DjangoEventRepository()
        self.piste_repository = piste_repository or DjangoPisteRepository()

    def get_pool_by_id(self, pool_id: UUID) -> Optional[Pool]:
        """Get pool by ID."""
        return self.pool_repository.get_pool_by_id(pool_id)

    def get_all_pools(self) -> List[Pool]:
        """Get all pools."""
        return self.pool_repository.get_all_pools()

    def get_pools_by_event(self, event_id: UUID) -> List[Pool]:
        """Get pools by event."""
        return self.pool_repository.get_pools_by_event(event_id)

    def get_active_pools(self) -> List[Pool]:
        """Get active pools."""
        return self.pool_repository.get_active_pools()

    def get_pools_with_stats(self, event_id: UUID) -> List[dict]:
        """Get pools with stats."""
        return self.pool_repository.get_pools_with_stats(event_id)

    def create_pool(self, pool_data: dict) -> Pool:
        """
        Create pool.

        Validation is done by Serializer.
        This method creates the domain entity and saves it.
        """
        self._validate_foreign_keys(pool_data)

        if not pool_data.get('pool_number'):
            pool_data['pool_number'] = self.pool_repository.get_next_pool_number(
                pool_data['event_id'] if 'event_id' in pool_data else pool_data['event'].id
            )

        event_id = pool_data.get('event_id') or (pool_data.get('event').id if pool_data.get('event') else None)

        pool = Pool(
            event_id=event_id,
            stage_id=pool_data.get('stage_id', '1'),
            pool_number=pool_data['pool_number'],
            fencer_ids=pool_data.get('fencer_ids', []),
            results=pool_data.get('results', []),
            stats=pool_data.get('stats', []),
            is_locked=pool_data.get('is_locked', False),
            status=pool_data.get('status', PoolStatus.SCHEDULED.value),
            is_completed=pool_data.get('is_completed', False)
        )

        try:
            return self.pool_repository.save_pool(pool)
        except IntegrityError as e:
            if 'unique_pool_event_number' in str(e):
                raise self.PoolServiceError(f"Pool number '{pool_data.get('pool_number')}' already exists in this event")
            raise self.PoolServiceError(f"Create pool failed: {str(e)}")

    def update_pool(self, pool_id: UUID, pool_data: dict) -> Pool:
        """
        Update pool.

        Validation is done by Serializer.
        This method updates the domain entity and saves it.
        """
        existing_pool = self.pool_repository.get_pool_by_id(pool_id)
        if not existing_pool:
            raise self.PoolServiceError(f"Pool {pool_id} not found")

        if 'status' in pool_data:
            self._validate_status_transition(existing_pool.status, pool_data['status'])

        self._validate_foreign_keys(pool_data)

        for key, value in pool_data.items():
            if hasattr(existing_pool, key):
                setattr(existing_pool, key, value)

        try:
            return self.pool_repository.save_pool(existing_pool)
        except IntegrityError as e:
            if 'unique_pool_event_number' in str(e):
                raise self.PoolServiceError(f"Pool number '{pool_data.get('pool_number')}' already exists in this event")
            raise self.PoolServiceError(f"Update pool failed: {str(e)}")

    def delete_pool(self, pool_id: UUID) -> bool:
        """Delete pool."""
        pool = self.pool_repository.get_pool_by_id(pool_id)
        if not pool:
            return False

        return self.pool_repository.delete_pool(pool_id)

    def update_pool_status(self, pool_id: UUID, status: str) -> Pool:
        """Update pool status."""
        pool = self.pool_repository.get_pool_by_id(pool_id)
        if not pool:
            raise self.PoolServiceError(f"Pool {pool_id} not found")

        self._validate_status_transition(pool.status, status)

        updated_pool = self.pool_repository.update_pool_status(pool_id, status)
        if not updated_pool:
            raise self.PoolServiceError("Update pool status failed")

        return updated_pool

    def _validate_foreign_keys(self, data: dict) -> None:
        """Validate foreign key existence."""
        event_id = None
        if 'event' in data and hasattr(data['event'], 'id'):
            event_id = data['event'].id
        elif 'event_id' in data:
            event_id = data['event_id']

        if event_id:
            event = self.event_repository.get_event_by_id(event_id)
            if not event:
                raise self.PoolServiceError(f"Event {event_id} not found")

        piste_id = data.get('piste_id')
        if piste_id:
            piste = self.piste_repository.get_by_id(piste_id)
            if not piste:
                raise self.PoolServiceError(f"Piste {piste_id} not found")

    def _validate_status_transition(self, current_status: str, new_status: str) -> None:
        """Validate status transition."""
        if current_status == new_status:
            return

        valid_transitions = STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in valid_transitions:
            raise self.PoolServiceError(
                f"Cannot transition from '{current_status}' to '{new_status}'. "
                f"Allowed transitions: {', '.join(valid_transitions)}"
            )

    class PoolServiceError(Exception):
        """Service layer exception."""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
