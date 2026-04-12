"""
End-to-end cluster test for bulk operations sync.
Verifies bulk-created records appear on follower node after applying sync logs.
"""

import pytest
from uuid import uuid4
from datetime import date
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from backend.apps.cluster.services.sync_manager import sync_manager
from backend.apps.cluster.models import DjangoSyncLog
from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament
from backend.apps.fencing_organizer.modules.event.models import DjangoEvent
from backend.apps.fencing_organizer.modules.pool.models import DjangoPool
from backend.apps.fencing_organizer.modules.event_participant.models import DjangoEventParticipant
from backend.apps.fencing_organizer.modules.pool_assignment.models import DjangoPoolAssignment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_api_client():
    client = APIClient()
    user = get_user_model().objects.create_user(username="testuser", password="testpass123", email="test@example.com")
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestBulkOperationsSync:
    """Test that bulk-created records are replicated to follower via sync logs."""

    def test_fencer_bulk_save_appears_on_follower(self, api_client):
        """
        Test fencer bulk-save creates sync logs, and follower applying those logs
        results in fencer records appearing in follower database.
        """
        # Ensure sync_manager has fencer model registered (should already be registered)
        if "fencer" not in sync_manager.get_registered_tables():
            from backend.apps.fencing_organizer.modules.fencer.serializers import FencerSerializer

            sync_manager.register_model(
                table_name="fencer",
                model_class=DjangoFencer,
                serializer_class=FencerSerializer,
                version_field="version",
                last_modified_field="updated_at",
            )

        # Step 1: Create a tournament (required for foreign key relationships in other tests)
        _tournament = DjangoTournament.objects.create(  # noqa: F841
            id=uuid4(),
            tournament_name="Test Tournament",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            status=DjangoTournament.Status.PLANNING,
            organizer=None,
            location=None,
        )

        # Step 2: Call the bulk_save endpoint for fencers using Django's APIClient
        fencer_data = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "MEN",
            "country_code": "USA",
        }
        response = api_client.post(
            "/api/fencers/bulk-save/",
            [fencer_data],
            format="json",
        )
        assert response.status_code == 200
        assert response.data["saved_count"] == 1
        assert response.data["error_count"] == 0
        results = response.data["results"]
        assert len(results) == 1
        created_fencer_id = results[0]["id"]

        # Step 3: Verify that sync logs are created in DjangoSyncLog for each record
        sync_logs = DjangoSyncLog.objects.filter(table_name="fencer", record_id=created_fencer_id, operation="INSERT")
        assert sync_logs.count() == 1
        sync_log = sync_logs.first()
        assert sync_log.id is not None
        assert sync_log.data["first_name"] == "John"

        # Step 4: Simulate a follower applying those sync logs using sync_manager.apply_change
        # First, delete the fencer record from the local database (simulating follower not having it yet)
        DjangoFencer.objects.filter(id=created_fencer_id).delete()
        assert not DjangoFencer.objects.filter(id=created_fencer_id).exists()

        # Apply the sync log as a follower would
        change = sync_manager.get_changes_since(since_id=0, limit=10)
        assert len(change.changes) >= 1
        # Find the change for our fencer
        fencer_change = None
        for c in change.changes:
            if c.table_name == "fencer" and c.record_id == created_fencer_id and c.operation == "INSERT":
                fencer_change = c
                break
        assert fencer_change is not None

        # Apply the change
        success = sync_manager.apply_change(fencer_change)
        assert success is True

        # Step 5: Verify that the records exist in the database after applying changes
        assert DjangoFencer.objects.filter(id=created_fencer_id).exists()
        fencer = DjangoFencer.objects.get(id=created_fencer_id)
        assert fencer.first_name == "John"
        assert fencer.last_name == "Doe"
        assert fencer.gender == "MEN"
        assert fencer.country_code == "USA"

    def test_event_participant_bulk_register_appears_on_follower(self, authenticated_api_client):
        """
        Test event-participant bulk-register creates sync logs, and follower applying those logs
        results in event participant records appearing in follower database.
        """
        # Ensure sync_manager has event_participant model registered
        if "event_participant" not in sync_manager.get_registered_tables():
            from backend.apps.fencing_organizer.modules.event_participant.serializers import EventParticipantSerializer

            sync_manager.register_model(
                table_name="event_participant",
                model_class=DjangoEventParticipant,
                serializer_class=EventParticipantSerializer,
                version_field="version",
                last_modified_field="updated_at",
            )

        # Step 1: Create tournament, event, and fencer
        _tournament = DjangoTournament.objects.create(
            id=uuid4(),
            tournament_name="Test Tournament",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            status=DjangoTournament.Status.PLANNING,
            organizer=None,
            location=None,
        )
        event = DjangoEvent.objects.create(
            id=uuid4(),
            event_name="Test Event",
            tournament_id=_tournament.id,
            event_type="MEN_INDIVIDUAL_FOIL",
            status="REGISTRATION",
            rule=None,
        )
        fencer = DjangoFencer.objects.create(
            id=uuid4(),
            first_name="Jane",
            last_name="Smith",
            gender="MEN",
            country_code="CAN",
        )

        # Step 2: Call bulk_register endpoint
        response = authenticated_api_client.post(
            "/api/event-participants/bulk-register/",
            {"event_id": str(event.id), "fencer_ids": [str(fencer.id)]},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["successful_count"] == 1
        assert response.data["failed_count"] == 0

        # Extract participant ID from response (assuming structure)
        # The response does not return participant IDs; we need to query the sync logs
        # Instead we'll query DjangoEventParticipant directly
        from backend.apps.fencing_organizer.modules.event_participant.models import DjangoEventParticipant

        participant = DjangoEventParticipant.objects.filter(event_id=event.id, fencer_id=fencer.id).first()
        assert participant is not None
        participant_id = participant.id

        # Step 3: Verify sync logs
        sync_logs = DjangoSyncLog.objects.filter(table_name="event_participant", record_id=str(participant_id), operation="INSERT")
        assert sync_logs.count() == 1

        # Step 4: Simulate follower applying sync logs
        DjangoEventParticipant.objects.filter(id=participant_id).delete()
        assert not DjangoEventParticipant.objects.filter(id=participant_id).exists()

        change = sync_manager.get_changes_since(since_id=0, limit=10)
        fencer_change = None
        for c in change.changes:
            if c.table_name == "event_participant" and c.record_id == str(participant_id) and c.operation == "INSERT":
                fencer_change = c
                break
        assert fencer_change is not None
        success = sync_manager.apply_change(fencer_change)
        assert success is True

        # Step 5: Verify record exists
        assert DjangoEventParticipant.objects.filter(id=participant_id).exists()

    def test_pool_assignment_bulk_create_appears_on_follower(self, authenticated_api_client):
        """
        Test pool-assignment bulk-create creates sync logs, and follower applying those logs
        results in pool assignment records appearing in follower database.
        """
        # Ensure sync_manager has pool_assignment model registered
        if "pool_assignment" not in sync_manager.get_registered_tables():
            from backend.apps.fencing_organizer.modules.pool_assignment.serializers import PoolAssignmentSerializer

            sync_manager.register_model(
                table_name="pool_assignment",
                model_class=DjangoPoolAssignment,
                serializer_class=PoolAssignmentSerializer,
                version_field="version",
                last_modified_field="updated_at",
            )

        # Step 1: Create tournament, event, pool, and fencer
        _tournament = DjangoTournament.objects.create(
            id=uuid4(),
            tournament_name="Test Tournament",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            status=DjangoTournament.Status.PLANNING,
            organizer=None,
            location=None,
        )
        event = DjangoEvent.objects.create(
            id=uuid4(),
            event_name="Test Event",
            tournament_id=_tournament.id,
            event_type="MEN_INDIVIDUAL_FOIL",
            status="REGISTRATION",
            rule=None,
        )
        pool = DjangoPool.objects.create(
            id=uuid4(),
            event_id=event.id,
            stage_id="1",
            pool_number=1,
        )
        fencer = DjangoFencer.objects.create(
            id=uuid4(),
            first_name="Alex",
            last_name="Johnson",
            gender="MEN",
            country_code="GBR",
        )
        # Register fencer to event (required for pool assignment)
        DjangoEventParticipant.objects.create(
            id=uuid4(),
            event_id=event.id,
            fencer_id=fencer.id,
        )

        # Step 2: Call bulk_create endpoint
        response = authenticated_api_client.post(
            "/api/pool-assignments/bulk-create/",
            {"pool_id": str(pool.id), "fencer_ids": [str(fencer.id)]},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["created_count"] == 1

        # Extract assignment ID
        from backend.apps.fencing_organizer.modules.pool_assignment.models import DjangoPoolAssignment

        assignment = DjangoPoolAssignment.objects.filter(pool_id=pool.id, fencer_id=fencer.id).first()
        assert assignment is not None
        assignment_id = assignment.id

        # Step 3: Verify sync logs
        sync_logs = DjangoSyncLog.objects.filter(table_name="pool_assignment", record_id=str(assignment_id), operation="INSERT")
        assert sync_logs.count() == 1

        # Step 4: Simulate follower applying sync logs
        DjangoPoolAssignment.objects.filter(id=assignment_id).delete()
        assert not DjangoPoolAssignment.objects.filter(id=assignment_id).exists()

        change = sync_manager.get_changes_since(since_id=0, limit=10)
        assignment_change = None
        for c in change.changes:
            if c.table_name == "pool_assignment" and c.record_id == str(assignment_id) and c.operation == "INSERT":
                assignment_change = c
                break
        assert assignment_change is not None
        success = sync_manager.apply_change(assignment_change)
        assert success is True

        # Step 5: Verify record exists
        assert DjangoPoolAssignment.objects.filter(id=assignment_id).exists()
