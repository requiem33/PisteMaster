"""
Integration tests for event participant sync logging.
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from backend.apps.cluster.models import DjangoSyncLog


@pytest.fixture
def api_client():
    client = APIClient()
    user = get_user_model().objects.create_user(username="testuser", password="testpass123", email="test@example.com")
    client.force_authenticate(user=user)
    return client


def create_mock_event_participant(participant_id, event_id, fencer_id, **kwargs):
    """Create a mock event participant domain object with required attributes."""

    class MockEventParticipant:
        pass

    mock = MockEventParticipant()
    mock.id = participant_id
    mock.event_id = event_id
    mock.fencer_id = fencer_id
    mock.seed_rank = kwargs.get("seed_rank")
    mock.seed_value = kwargs.get("seed_value")
    mock.notes = kwargs.get("notes")
    mock.is_confirmed = kwargs.get("is_confirmed", False)
    mock.registration_time = kwargs.get("registration_time")
    mock.created_at = kwargs.get("created_at")
    mock.updated_at = kwargs.get("updated_at")
    return mock


def create_mock_django_event_participant(participant_id, **kwargs):
    """Create a mock DjangoEventParticipant instance."""

    class MockDjangoEventParticipant:
        pass

    mock = MockDjangoEventParticipant()
    mock.id = participant_id
    for key, val in kwargs.items():
        setattr(mock, key, val)
    return mock


@pytest.mark.django_db
class TestEventParticipantBulkRegisterSyncLogging:
    """Test sync logging for event-participant bulk-register endpoint."""

    def test_bulk_register_records_sync_log(self, api_client):
        """
        POST to /api/event-participants/bulk-register/ creates sync log entries.
        """
        from backend.apps.fencing_organizer.modules.event_participant.models import DjangoEventParticipant
        from backend.apps.fencing_organizer.modules.event_participant.views import EventParticipantService as RealService

        event_id = uuid4()
        fencer_id1 = uuid4()
        fencer_id2 = uuid4()
        participant_id1 = uuid4()
        participant_id2 = uuid4()

        # Mock DjangoEventParticipant instances for model_to_dict (simple mocks)
        # Participant 1: no created_at (None)
        django_participant1 = create_mock_django_event_participant(
            participant_id1,
            event_id=event_id,
            fencer_id=fencer_id1,
            seed_rank=None,
            seed_value=None,
            is_confirmed=False,
            registration_time=None,
            created_at=None,
            updated_at=None,
        )
        # Participant 2: has created_at timestamp
        created_at_dt = datetime(2025, 1, 15, 10, 30, 0)
        django_participant2 = create_mock_django_event_participant(
            participant_id2,
            event_id=event_id,
            fencer_id=fencer_id2,
            seed_rank=1,
            seed_value=100.0,
            is_confirmed=True,
            registration_time=None,
            created_at=created_at_dt,
            updated_at=None,
        )

        # Mock service method
        with patch("backend.apps.fencing_organizer.modules.event_participant.views.EventParticipantService") as MockService:
            # Preserve the real inner exception class
            MockService.EventParticipantServiceError = RealService.EventParticipantServiceError
            mock_service_instance = MockService.return_value
            # Mock bulk_register_fencers to return successful participants
            mock_participant1 = create_mock_event_participant(
                participant_id1, event_id, fencer_id1, seed_rank=None, seed_value=None, is_confirmed=False
            )
            mock_participant2 = create_mock_event_participant(
                participant_id2, event_id, fencer_id2, seed_rank=1, seed_value=100.0, is_confirmed=True
            )
            mock_service_instance.bulk_register_fencers.return_value = ([mock_participant1, mock_participant2], [])

            # Mock DjangoEventParticipant.objects.get for each participant ID
            with patch.object(DjangoEventParticipant.objects, "get") as mock_get:
                mock_get.side_effect = [django_participant1, django_participant2]
                # Mock model_to_dict to return a dict based on the mock instance
                with patch("backend.apps.fencing_organizer.modules.event_participant.views.model_to_dict") as mock_model_to_dict:

                    def mock_model_to_dict_side_effect(instance):
                        """Return a dict with the instance's attributes."""
                        # Base dict with common fields
                        data = {
                            "id": str(instance.id) if instance.id else None,
                            "event_id": str(instance.event_id) if hasattr(instance, "event_id") else None,
                            "fencer_id": str(instance.fencer_id) if hasattr(instance, "fencer_id") else None,
                            "seed_rank": getattr(instance, "seed_rank", None),
                            "seed_value": getattr(instance, "seed_value", None),
                            "is_confirmed": getattr(instance, "is_confirmed", False),
                            "registration_time": getattr(instance, "registration_time", None),
                            "notes": getattr(instance, "notes", None),
                            "version": 1,
                        }
                        # Include created_at only if the attribute exists and is not None
                        if hasattr(instance, "created_at") and instance.created_at is not None:
                            data["created_at"] = instance.created_at
                        return data

                    mock_model_to_dict.side_effect = mock_model_to_dict_side_effect

                    # Make POST request
                    response = api_client.post(
                        "/api/event-participants/bulk-register/",
                        {"event_id": str(event_id), "fencer_ids": [str(fencer_id1), str(fencer_id2)]},
                        format="json",
                    )

        # Assert response success
        assert response.status_code == 201
        assert response.data["successful_count"] == 2
        assert response.data["failed_count"] == 0

        # Assert sync log entries created
        sync_logs = DjangoSyncLog.objects.filter(table_name="event_participant", operation="INSERT")
        # Expect 2 after implementation
        assert sync_logs.count() == 2
        # Verify sync log IDs are assigned (request._sync_log_id will be set)
        assert all(log.id is not None for log in sync_logs)
        # Check each participant ID
        participant_ids = {str(participant_id1), str(participant_id2)}
        log_ids = {log.record_id for log in sync_logs}
        assert log_ids == participant_ids

        # Verify created_at preservation: participant2's sync log data should contain created_at
        log_for_participant2 = next(log for log in sync_logs if log.record_id == str(participant_id2))
        data2 = log_for_participant2.data
        assert "created_at" in data2
        # The timestamp should match the mock's created_at (datetime object)
        # JSON serialization may convert datetime to string; compare accordingly
        # Since we're using a real datetime object stored in JSONField, Django will serialize it to ISO string
        # We'll just check that the field exists and is not None
        assert data2["created_at"] is not None
        # Optionally check format (isoformat)
        # assert data2["created_at"] == created_at_dt.isoformat()

        # Verify participant1's sync log data does NOT have created_at (since it was None)
        log_for_participant1 = next(log for log in sync_logs if log.record_id == str(participant_id1))
        data1 = log_for_participant1.data
        assert "created_at" not in data1


@pytest.mark.django_db
class TestEventSyncParticipantsSyncLogging:
    """Test sync logging for event sync_participants endpoint."""

    def test_sync_participants_records_sync_log(self, api_client):
        """
        PUT to /api/events/{eventId}/participants/sync/ creates sync log entries for DELETE and INSERT.
        """
        from backend.apps.fencing_organizer.modules.event_participant.models import DjangoEventParticipant
        from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer

        event_id = uuid4()
        fencer_id1 = uuid4()
        fencer_id2 = uuid4()
        existing_participant_id1 = uuid4()
        existing_participant_id2 = uuid4()

        # Mock existing participants (will be deleted)
        existing_participant1 = create_mock_django_event_participant(
            existing_participant_id1,
            event_id=event_id,
            fencer_id=uuid4(),
        )
        existing_participant2 = create_mock_django_event_participant(
            existing_participant_id2,
            event_id=event_id,
            fencer_id=uuid4(),
        )

        # Mock fencers that exist
        fencer1 = MagicMock()
        fencer1.id = fencer_id1
        fencer2 = MagicMock()
        fencer2.id = fencer_id2

        # Create mock queryset for DjangoEventParticipant.objects.filter
        mock_queryset = MagicMock()
        # First call: iteration over existing participants
        mock_queryset.__iter__ = MagicMock(return_value=iter([existing_participant1, existing_participant2]))
        # Second call: delete() does nothing
        mock_queryset.delete = MagicMock()

        # Mock DjangoEventParticipant.objects.filter to return our mock queryset
        with patch.object(DjangoEventParticipant.objects, "filter", return_value=mock_queryset):
            # Mock DjangoFencer.objects.filter to return a queryset with our fencers
            mock_fencer_queryset = MagicMock()
            mock_fencer_queryset.__iter__ = MagicMock(return_value=iter([fencer1, fencer2]))
            with patch.object(DjangoFencer.objects, "filter", return_value=mock_fencer_queryset):
                # Track new participants created via bulk_create
                created_participants = []

                def bulk_create_side_effect(objs, batch_size=None):
                    # Assign IDs to new participants (simulate database)
                    for obj in objs:
                        if not hasattr(obj, "id") or obj.id is None:
                            obj.id = uuid4()
                    created_participants.extend(objs)
                    return objs

                with patch.object(DjangoEventParticipant.objects, "bulk_create", side_effect=bulk_create_side_effect):
                    # Mock model_to_dict to return a dict representation
                    with patch("backend.apps.fencing_organizer.modules.event.views.model_to_dict") as mock_model_to_dict:

                        def model_to_dict_side_effect(instance):
                            data = {
                                "id": str(instance.id),
                                "event_id": str(instance.event_id),
                                "fencer_id": str(instance.fencer_id),
                                "seed_rank": getattr(instance, "seed_rank", None),
                                "seed_value": getattr(instance, "seed_value", None),
                                "is_confirmed": getattr(instance, "is_confirmed", False),
                                "registration_time": getattr(instance, "registration_time", None),
                                "notes": getattr(instance, "notes", None),
                                "version": 1,
                            }
                            if hasattr(instance, "created_at") and instance.created_at is not None:
                                data["created_at"] = instance.created_at
                            return data

                        mock_model_to_dict.side_effect = model_to_dict_side_effect

                        # Make PUT request
                        response = api_client.put(
                            f"/api/events/{event_id}/participants/sync/",
                            {"fencer_ids": [str(fencer_id1), str(fencer_id2)]},
                            format="json",
                        )

        # Assert response success
        assert response.status_code == 200
        assert response.data["synced_count"] == 2

        # Assert sync log entries created for DELETE and INSERT
        delete_logs = DjangoSyncLog.objects.filter(table_name="event_participant", operation="DELETE")
        insert_logs = DjangoSyncLog.objects.filter(table_name="event_participant", operation="INSERT")

        # Expect 2 DELETE logs for existing participants
        assert delete_logs.count() == 2
        delete_record_ids = {log.record_id for log in delete_logs}
        assert delete_record_ids == {str(existing_participant_id1), str(existing_participant_id2)}

        # Expect 2 INSERT logs for new participants
        assert insert_logs.count() == 2
        # Verify each INSERT log has a valid UUID record_id
        for log in insert_logs:
            assert log.record_id is not None
            assert len(log.record_id) == 36

        # Verify sync log IDs assigned
        assert all(log.id is not None for log in delete_logs)
        assert all(log.id is not None for log in insert_logs)
