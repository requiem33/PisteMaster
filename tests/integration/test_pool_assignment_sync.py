"""
Integration tests for pool assignment sync logging.
"""

import pytest
from unittest.mock import patch
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


def create_mock_pool_assignment(assignment_id, pool_id, fencer_id, **kwargs):
    """Create a mock pool assignment domain object with required attributes."""

    class MockPoolAssignment:
        pass

    mock = MockPoolAssignment()
    mock.id = assignment_id
    mock.pool_id = pool_id
    mock.fencer_id = fencer_id
    mock.final_pool_rank = kwargs.get("final_pool_rank")
    mock.victories = kwargs.get("victories", 0)
    mock.indicator = kwargs.get("indicator", 0)
    mock.touches_scored = kwargs.get("touches_scored", 0)
    mock.touches_received = kwargs.get("touches_received", 0)
    mock.is_qualified = kwargs.get("is_qualified", False)
    mock.qualification_rank = kwargs.get("qualification_rank")
    mock.created_at = kwargs.get("created_at")
    mock.updated_at = kwargs.get("updated_at")
    return mock


def create_mock_django_pool_assignment(assignment_id, **kwargs):
    """Create a mock DjangoPoolAssignment instance."""

    class MockDjangoPoolAssignment:
        pass

    mock = MockDjangoPoolAssignment()
    mock.id = assignment_id
    for key, val in kwargs.items():
        setattr(mock, key, val)
    return mock


@pytest.mark.django_db
class TestPoolAssignmentBulkCreateSyncLogging:
    """Test sync logging for pool-assignment bulk-create endpoint."""

    def test_bulk_create_records_sync_log(self, api_client):
        """
        POST to /api/pool-assignments/bulk-create/ creates sync log entries.
        """
        from backend.apps.fencing_organizer.modules.pool_assignment.models import DjangoPoolAssignment
        from backend.apps.fencing_organizer.modules.pool_assignment.views import PoolAssignmentService as RealService

        pool_id = uuid4()
        fencer_id1 = uuid4()
        fencer_id2 = uuid4()
        assignment_id1 = uuid4()
        assignment_id2 = uuid4()

        # Mock DjangoPoolAssignment instances for model_to_dict
        # Assignment 1: no created_at (None)
        django_assignment1 = create_mock_django_pool_assignment(
            assignment_id1,
            pool_id=pool_id,
            fencer_id=fencer_id1,
            final_pool_rank=None,
            victories=0,
            indicator=0,
            touches_scored=0,
            touches_received=0,
            is_qualified=False,
            qualification_rank=None,
            created_at=None,
            updated_at=None,
        )
        # Assignment 2: has created_at timestamp
        created_at_dt = datetime(2025, 1, 15, 10, 30, 0)
        django_assignment2 = create_mock_django_pool_assignment(
            assignment_id2,
            pool_id=pool_id,
            fencer_id=fencer_id2,
            final_pool_rank=1,
            victories=3,
            indicator=5,
            touches_scored=15,
            touches_received=10,
            is_qualified=True,
            qualification_rank=1,
            created_at=created_at_dt,
            updated_at=None,
        )

        # Mock service method
        with patch("backend.apps.fencing_organizer.modules.pool_assignment.views.PoolAssignmentService") as MockService:
            # Preserve the real inner exception class
            MockService.PoolAssignmentServiceError = RealService.PoolAssignmentServiceError
            mock_service_instance = MockService.return_value
            # Mock assign_fencers_to_pool to return assignments
            mock_assignment1 = create_mock_pool_assignment(
                assignment_id1,
                pool_id,
                fencer_id1,
                final_pool_rank=None,
                victories=0,
                indicator=0,
                touches_scored=0,
                touches_received=0,
                is_qualified=False,
                qualification_rank=None,
                created_at=None,
            )
            mock_assignment2 = create_mock_pool_assignment(
                assignment_id2,
                pool_id,
                fencer_id2,
                final_pool_rank=1,
                victories=3,
                indicator=5,
                touches_scored=15,
                touches_received=10,
                is_qualified=True,
                qualification_rank=1,
                created_at=created_at_dt,
            )
            mock_service_instance.assign_fencers_to_pool.return_value = [mock_assignment1, mock_assignment2]

            # Mock DjangoPoolAssignment.objects.get for each assignment ID
            with patch.object(DjangoPoolAssignment.objects, "get") as mock_get:
                mock_get.side_effect = [django_assignment1, django_assignment2]
                # Mock model_to_dict to return a dict based on the mock instance
                with patch("backend.apps.fencing_organizer.modules.pool_assignment.views.model_to_dict", create=True) as mock_model_to_dict:

                    def mock_model_to_dict_side_effect(instance):
                        """Return a dict with the instance's attributes."""
                        data = {
                            "id": str(instance.id) if instance.id else None,
                            "pool_id": str(instance.pool_id) if hasattr(instance, "pool_id") else None,
                            "fencer_id": str(instance.fencer_id) if hasattr(instance, "fencer_id") else None,
                            "final_pool_rank": getattr(instance, "final_pool_rank", None),
                            "victories": getattr(instance, "victories", 0),
                            "indicator": getattr(instance, "indicator", 0),
                            "touches_scored": getattr(instance, "touches_scored", 0),
                            "touches_received": getattr(instance, "touches_received", 0),
                            "is_qualified": getattr(instance, "is_qualified", False),
                            "qualification_rank": getattr(instance, "qualification_rank", None),
                            "version": 1,
                        }
                        # Include created_at only if the attribute exists and is not None
                        if hasattr(instance, "created_at") and instance.created_at is not None:
                            data["created_at"] = instance.created_at
                        return data

                    mock_model_to_dict.side_effect = mock_model_to_dict_side_effect

                    # Make POST request
                    response = api_client.post(
                        "/api/pool-assignments/bulk-create/",
                        {"pool_id": str(pool_id), "fencer_ids": [str(fencer_id1), str(fencer_id2)]},
                        format="json",
                    )

        # Assert response success
        assert response.status_code == 201
        assert response.data["pool_id"] == str(pool_id)
        assert response.data["created_count"] == 2

        # Assert sync log entries created
        sync_logs = DjangoSyncLog.objects.filter(table_name="pool_assignment", operation="INSERT")
        # Expect 2 after implementation
        assert sync_logs.count() == 2
        # Verify sync log IDs are assigned (request._sync_log_id will be set)
        assert all(log.id is not None for log in sync_logs)
        # Check each assignment ID
        assignment_ids = {str(assignment_id1), str(assignment_id2)}
        log_ids = {log.record_id for log in sync_logs}
        assert log_ids == assignment_ids

        # Verify created_at preservation: assignment2's sync log data should contain created_at
        log_for_assignment2 = next(log for log in sync_logs if log.record_id == str(assignment_id2))
        data2 = log_for_assignment2.data
        assert "created_at" in data2
        assert data2["created_at"] is not None

        # Verify assignment1's sync log data does NOT have created_at (since it was None)
        log_for_assignment1 = next(log for log in sync_logs if log.record_id == str(assignment_id1))
        data1 = log_for_assignment1.data
        assert "created_at" not in data1
