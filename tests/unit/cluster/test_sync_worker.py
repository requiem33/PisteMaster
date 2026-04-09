"""Tests for SyncWorker — background sync thread for follower nodes."""

import threading
from unittest.mock import patch, MagicMock

from backend.apps.cluster.services.sync_worker import SyncWorker


class TestSyncWorkerInit:
    def test_initial_state(self):
        worker = SyncWorker()
        assert worker._running is False
        assert worker._thread is None
        assert worker.is_running is False


class TestSyncWorkerStartStop:
    @patch("backend.apps.cluster.services.sync_worker.DjangoClusterConfig")
    def test_start_as_follower(self, mock_config_cls):
        config = MagicMock()
        config.mode = "cluster"
        config.is_master = False
        config.node_id = "follower_001"
        config.master_url = "http://master:8000"
        mock_config_cls.get_config.return_value = config

        worker = SyncWorker()
        worker._do_sync_cycle = MagicMock()

        with patch.object(worker, "_sync_loop"):
            worker.start()

        assert worker._running is True
        worker.stop()

    @patch("backend.apps.cluster.services.sync_worker.DjangoClusterConfig")
    def test_start_skips_if_master(self, mock_config_cls):
        config = MagicMock()
        config.mode = "cluster"
        config.is_master = True
        config.node_id = "master_001"
        mock_config_cls.get_config.return_value = config

        worker = SyncWorker()
        worker.start()

        assert worker._running is False

    @patch("backend.apps.cluster.services.sync_worker.DjangoClusterConfig")
    def test_start_skips_if_single_mode(self, mock_config_cls):
        config = MagicMock()
        config.mode = "single"
        config.is_master = False
        mock_config_cls.get_config.return_value = config

        worker = SyncWorker()
        worker.start()

        assert worker._running is False

    def test_stop_sets_stop_event(self):
        worker = SyncWorker()
        worker._stop_event = threading.Event()
        worker._sync_event = threading.Event()
        worker.stop()

        assert worker._stop_event.is_set()


class TestSyncWorkerTriggerImmediateSync:
    def test_trigger_sets_sync_event(self):
        worker = SyncWorker()
        worker._sync_event = threading.Event()

        assert not worker._sync_event.is_set()
        worker.trigger_immediate_sync()
        assert worker._sync_event.is_set()


class TestSyncWorkerDoSyncCycle:
    @patch("backend.apps.cluster.services.sync_worker.DjangoClusterConfig")
    def test_skips_if_master_node(self, mock_config_cls):
        config = MagicMock()
        config.mode = "cluster"
        config.is_master = True
        config.node_id = "node_001"
        mock_config_cls.get_config.return_value = config

        worker = SyncWorker()
        worker._running = True

        with patch("backend.apps.cluster.services.sync_worker.requests") as mock_requests:
            worker._do_sync_cycle()
            mock_requests.get.assert_not_called()

    @patch("backend.apps.cluster.services.sync_worker.DjangoClusterConfig")
    def test_skips_if_no_master_url(self, mock_config_cls):
        config = MagicMock()
        config.mode = "cluster"
        config.is_master = False
        config.node_id = "node_001"
        config.master_url = None
        mock_config_cls.get_config.return_value = config

        worker = SyncWorker()

        with patch("backend.apps.cluster.services.sync_worker.requests") as mock_requests:
            worker._do_sync_cycle()
            mock_requests.get.assert_not_called()


class TestSyncWorkerDoIncrementalSync:
    @patch("backend.apps.cluster.services.sync_worker.sync_manager")
    @patch("backend.apps.cluster.services.sync_worker.requests")
    @patch("backend.apps.cluster.services.sync_worker.DjangoClusterConfig")
    def test_incremental_sync_applies_changes(self, mock_config_cls, mock_requests, mock_sync_manager):
        config = MagicMock()
        config.mode = "cluster"
        config.is_master = False
        config.node_id = "follower_001"
        config.master_url = "http://master:8000"
        config.sync_interval = 3.0
        mock_config_cls.get_config.return_value = config

        mock_state = MagicMock()
        mock_state.last_synced_id = 10
        mock_sync_manager.get_sync_state.return_value = mock_state

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "changes": [
                {
                    "id": 11,
                    "table_name": "tournament",
                    "record_id": "t1",
                    "operation": "CREATE",
                    "data": {"name": "Test"},
                    "version": 1,
                    "created_at": None,
                }
            ],
            "last_id": 11,
            "has_more": False,
        }
        mock_requests.get.return_value = mock_response

        mock_sync_manager.apply_changes_batch.return_value = {"success": 1, "failed": 0, "skipped": 0}

        worker = SyncWorker()
        with patch.object(worker, "_send_ack"):
            worker._do_incremental_sync("http://master:8000", "follower_001", 10)

        mock_sync_manager.apply_changes_batch.assert_called_once()
        mock_sync_manager.update_sync_state.assert_called_once_with("follower_001", 11)


class TestSyncWorkerSendAck:
    @patch("backend.apps.cluster.services.sync_worker.requests")
    def test_send_ack_posts_to_master(self, mock_requests):
        worker = SyncWorker()
        worker._send_ack("http://master:8000", "follower_001", 42)

        mock_requests.post.assert_called_once_with(
            "http://master:8000/api/cluster/sync/ack/",
            json={"node_id": "follower_001", "sync_id": 42},
            timeout=5,
        )

    @patch("backend.apps.cluster.services.sync_worker.requests")
    def test_send_ack_handles_failure(self, mock_requests):
        from requests.exceptions import RequestException

        mock_requests.post.side_effect = RequestException("Connection refused")
        mock_requests.RequestException = RequestException

        worker = SyncWorker()
        worker._send_ack("http://master:8000", "follower_001", 42)
