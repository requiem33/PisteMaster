"""
Integration tests for event participant sync logging.
"""

import pytest
from unittest.mock import patch
from uuid import uuid4
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
        django_participant2 = create_mock_django_event_participant(
            participant_id2,
            event_id=event_id,
            fencer_id=fencer_id2,
            seed_rank=1,
            seed_value=100.0,
            is_confirmed=True,
            registration_time=None,
            created_at=None,
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
                # Mock model_to_dict to return a simple dict (patch the imported function in views)
                with patch("backend.apps.fencing_organizer.modules.event_participant.views.model_to_dict") as mock_model_to_dict:
                    mock_model_to_dict.return_value = {
                        "id": None,  # will be overridden by record_insert anyway
                        "event_id": str(event_id),
                        "fencer_id": None,
                        "seed_rank": None,
                        "seed_value": None,
                        "is_confirmed": False,
                        "registration_time": None,
                        "notes": None,
                        "version": 1,
                    }

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
        # Check each participant ID
        participant_ids = {str(participant_id1), str(participant_id2)}
        log_ids = {log.record_id for log in sync_logs}
        assert log_ids == participant_ids
