"""Tests for cluster sync API endpoints."""

import pytest
from rest_framework.test import APIClient

from backend.apps.cluster.models import DjangoSyncLog, DjangoSyncState, DjangoClusterConfig


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def cluster_config(db):
    config = DjangoClusterConfig.get_config()
    config.mode = "cluster"
    config.is_master = True
    config.node_id = "master_001"
    config.save()
    return config


@pytest.mark.django_db
class TestSyncNotifyEndpoint:
    def test_notify_returns_notified_on_follower(self, api_client, db):
        config = DjangoClusterConfig.get_config()
        config.mode = "cluster"
        config.is_master = False
        config.node_id = "follower_001"
        config.save()

        response = api_client.post(
            "/api/cluster/sync/notify/",
            {"sync_log_id": 1, "table_name": "tournament", "record_id": "abc"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "notified"

    def test_notify_returns_ignored_on_master(self, api_client, db):
        config = DjangoClusterConfig.get_config()
        config.mode = "cluster"
        config.is_master = True
        config.node_id = "master_001"
        config.save()

        response = api_client.post(
            "/api/cluster/sync/notify/",
            {"sync_log_id": 1, "table_name": "tournament", "record_id": "abc"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "ignored"


@pytest.mark.django_db
class TestSyncAckEndpoint:
    def test_ack_updates_sync_state(self, api_client, db):
        config = DjangoClusterConfig.get_config()
        config.mode = "cluster"
        config.is_master = True
        config.node_id = "master_001"
        config.save()

        response = api_client.post(
            "/api/cluster/sync/ack/",
            {"node_id": "follower_001", "sync_id": 10},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "acknowledged"

        state = DjangoSyncState.objects.get(node_id="follower_001")
        assert state.last_synced_id == 10

    def test_ack_with_url_stores_url(self, api_client, db):
        config = DjangoClusterConfig.get_config()
        config.mode = "cluster"
        config.is_master = True
        config.node_id = "master_001"
        config.save()

        response = api_client.post(
            "/api/cluster/sync/ack/",
            {"node_id": "follower_001", "sync_id": 5, "url": "http://192.168.1.10:8000"},
            format="json",
        )
        assert response.status_code == 200

        state = DjangoSyncState.objects.get(node_id="follower_001")
        assert state.url == "http://192.168.1.10:8000"
        assert state.last_synced_id == 5


@pytest.mark.django_db
class TestSyncApplyEndpoint:
    def test_apply_changes_creates_sync_state(self, api_client, db):
        config = DjangoClusterConfig.get_config()
        config.mode = "cluster"
        config.is_master = False
        config.node_id = "follower_001"
        config.save()

        sync_log = DjangoSyncLog.objects.create(
            table_name="tournament",
            record_id="test-1",
            operation="CREATE",
            data={"name": "Test Tournament"},
        )

        changes = [
            {
                "id": sync_log.id,
                "table_name": "tournament",
                "record_id": "test-1",
                "operation": "CREATE",
                "data": {"name": "Test Tournament"},
                "version": 1,
            }
        ]

        response = api_client.post(
            "/api/cluster/sync/apply/",
            {"changes": changes, "node_id": "follower_001", "url": "http://192.168.1.10:8000"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "applied"

        state = DjangoSyncState.objects.get(node_id="follower_001")
        assert state.last_synced_id == sync_log.id
        assert state.url == "http://192.168.1.10:8000"

    def test_apply_empty_changes(self, api_client, db):
        response = api_client.post(
            "/api/cluster/sync/apply/",
            {"changes": []},
            format="json",
        )
        assert response.status_code == 200

    def test_apply_invalid_changes(self, api_client, db):
        response = api_client.post(
            "/api/cluster/sync/apply/",
            {"changes": "not a list"},
            format="json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestAnnounceEndpoint:
    def test_announce_stores_url(self, api_client, db):
        config = DjangoClusterConfig.get_config()
        config.mode = "cluster"
        config.is_master = True
        config.node_id = "master_001"
        config.save()

        response = api_client.post(
            "/api/cluster/status/announce/",
            {
                "node_id": "follower_001",
                "ip": "192.168.1.10",
                "port": 8000,
                "url": "http://192.168.1.10:8000",
            },
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "announced"

        state = DjangoSyncState.objects.get(node_id="follower_001")
        assert state.url == "http://192.168.1.10:8000"

    def test_announce_constructs_url_from_ip_port(self, api_client, db):
        config = DjangoClusterConfig.get_config()
        config.mode = "cluster"
        config.is_master = True
        config.node_id = "master_001"
        config.save()

        response = api_client.post(
            "/api/cluster/status/announce/",
            {
                "node_id": "follower_002",
                "ip": "192.168.1.20",
                "port": 9000,
            },
            format="json",
        )
        assert response.status_code == 200

        state = DjangoSyncState.objects.get(node_id="follower_002")
        assert state.url == "http://192.168.1.20:9000"
