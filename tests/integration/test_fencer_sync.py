"""
Integration tests for fencer sync logging.
"""

import pytest
from unittest.mock import patch
from uuid import uuid4
from rest_framework.test import APIClient

from backend.apps.cluster.models import DjangoSyncLog
from backend.apps.fencing_organizer.modules.fencer.views import FencerViewSet


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def fencer_viewset():
    return FencerViewSet()


def create_mock_fencer(fencer_id, first_name, last_name, gender, country_code, **kwargs):
    """Create a mock fencer domain object with required attributes."""

    # Use a simple object
    class MockFencer:
        pass

    mock = MockFencer()
    mock.id = fencer_id
    mock.first_name = first_name
    mock.last_name = last_name
    mock.gender = gender
    mock.country_code = country_code
    mock.birth_date = kwargs.get("birth_date")
    mock.fencing_id = kwargs.get("fencing_id")
    mock.current_ranking = kwargs.get("current_ranking")
    mock.primary_weapon = kwargs.get("primary_weapon")
    mock.created_at = kwargs.get("created_at")
    mock.updated_at = kwargs.get("updated_at")
    mock.display_name = kwargs.get("display_name", f"{last_name} {first_name}")
    return mock


def create_mock_django_fencer(fencer_id, **kwargs):
    """Create a mock DjangoFencer instance."""

    class MockDjangoFencer:
        pass

    mock = MockDjangoFencer()
    mock.id = fencer_id
    for key, val in kwargs.items():
        setattr(mock, key, val)
    return mock


@pytest.mark.django_db
class TestFencerBulkSaveSyncLogging:
    """Test sync logging for fencer bulk-save endpoint."""

    def test_bulk_save_records_sync_log_for_new_fencers(self, api_client):
        """
        POST to /api/fencers/bulk-save/ with new fencers creates sync log entries.
        """
        from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer

        # Create mock fencer data
        fencer_id = uuid4()
        fencer_data = {
            "id": str(fencer_id),
            "first_name": "John",
            "last_name": "Doe",
            "gender": "M",
            "country_code": "USA",
        }

        # Create a DjangoFencer instance (unsaved) for model_to_dict
        django_fencer = DjangoFencer(
            id=fencer_id,
            first_name="John",
            last_name="Doe",
            gender="M",
            country_code="USA",
            created_at=None,
        )

        # Mock service methods
        with patch.object(FencerViewSet, "service") as mock_service:
            # Mock get_fencer_by_id to return None (new fencer)
            mock_service.get_fencer_by_id.return_value = None
            # Mock create_fencer to return a domain fencer
            mock_fencer = create_mock_fencer(
                fencer_id,
                first_name="John",
                last_name="Doe",
                gender="M",
                country_code="USA",
                birth_date=None,
                fencing_id=None,
                current_ranking=None,
                primary_weapon=None,
                created_at=None,
                updated_at=None,
            )
            mock_service.create_fencer.return_value = mock_fencer

            # Mock queryset.get to return our DjangoFencer instance
            with patch.object(FencerViewSet, "queryset") as mock_queryset:
                mock_queryset.get.return_value = django_fencer

                # Make POST request
                response = api_client.post(
                    "/api/fencers/bulk-save/",
                    [fencer_data],
                    format="json",
                )

        # Assert response success
        assert response.status_code == 200
        assert response.data["saved_count"] == 1
        assert response.data["error_count"] == 0

        # Assert sync log entry created
        sync_logs = DjangoSyncLog.objects.filter(table_name="fencer", record_id=str(fencer_id), operation="INSERT")
        # Expect 1 after implementation
        assert sync_logs.count() == 1
        sync_log = sync_logs.first()
        # Check data contains expected fields
        assert sync_log.data["first_name"] == "John"
        assert sync_log.data["last_name"] == "Doe"

    def test_bulk_save_updates_do_not_record_insert(self, api_client):
        """
        When bulk-save updates an existing fencer, no INSERT sync log is recorded.
        Updates are already logged by the wrapped update method.
        """
        existing_fencer_id = uuid4()
        fencer_data = {
            "id": str(existing_fencer_id),
            "first_name": "Jane",
            "last_name": "Smith",
            "gender": "F",
            "country_code": "CAN",
        }

        with patch.object(FencerViewSet, "service") as mock_service:
            # Mock get_fencer_by_id to return existing fencer
            mock_existing = create_mock_fencer(
                existing_fencer_id,
                first_name="Jane",
                last_name="Smith",
                gender="F",
                country_code="CAN",
            )
            mock_service.get_fencer_by_id.return_value = mock_existing
            # Mock update_fencer to return updated fencer
            mock_updated = create_mock_fencer(
                existing_fencer_id,
                first_name="Jane",
                last_name="Smith",
                gender="F",
                country_code="CAN",
            )
            mock_service.update_fencer.return_value = mock_updated

            # No need to mock queryset.get because INSERT not recorded

            response = api_client.post(
                "/api/fencers/bulk-save/",
                [fencer_data],
                format="json",
            )

        assert response.status_code == 200
        assert response.data["saved_count"] == 1

        # No INSERT sync log should be created
        insert_logs = DjangoSyncLog.objects.filter(table_name="fencer", record_id=str(existing_fencer_id), operation="INSERT")
        assert insert_logs.count() == 0
        # UPDATE logs may be created by wrapped update method, but we don't assert here

    def test_bulk_save_without_id_creates_insert_log(self, api_client):
        """
        Fencer data without ID creates new fencer and INSERT sync log.
        """
        from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer

        new_fencer_id = uuid4()
        fencer_data = {
            "first_name": "Alice",
            "last_name": "Wonder",
            "gender": "F",
            "country_code": "GBR",
        }

        # Create a DjangoFencer instance (unsaved) for model_to_dict
        django_fencer = DjangoFencer(
            id=new_fencer_id,
            first_name="Alice",
            last_name="Wonder",
            gender="F",
            country_code="GBR",
            created_at=None,
        )

        with patch.object(FencerViewSet, "service") as mock_service:
            # Mock create_fencer to return a new fencer with generated ID
            mock_fencer = create_mock_fencer(
                new_fencer_id,
                first_name="Alice",
                last_name="Wonder",
                gender="F",
                country_code="GBR",
            )
            mock_service.create_fencer.return_value = mock_fencer

            with patch.object(FencerViewSet, "queryset") as mock_queryset:
                mock_queryset.get.return_value = django_fencer

                response = api_client.post(
                    "/api/fencers/bulk-save/",
                    [fencer_data],
                    format="json",
                )

        assert response.status_code == 200
        assert response.data["saved_count"] == 1

        insert_logs = DjangoSyncLog.objects.filter(table_name="fencer", record_id=str(new_fencer_id), operation="INSERT")
        assert insert_logs.count() == 1
