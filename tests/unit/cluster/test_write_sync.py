"""Tests for SyncWriteMiddleware — _wait_for_acks and _notify_followers."""

import threading
import time
from unittest.mock import patch, MagicMock

from backend.apps.cluster.services.ack_queue import AckQueue


class TestWaitForAcks:
    def test_wait_returns_true_when_event_set(self):
        queue = AckQueue()
        queue.set_nodes_required(1)
        event = queue.register(1, 1)

        threading.Thread(target=lambda: event.set(), daemon=True).start()

        result = event.wait(timeout=1.0)
        assert result is True

    def test_wait_returns_false_on_timeout(self):
        queue = AckQueue()
        queue.set_nodes_required(2)
        event = queue.register(1, 2)

        result = event.wait(timeout=0.05)
        assert result is False

    def test_ack_sets_event(self):
        queue = AckQueue()
        queue.set_nodes_required(1)
        event = queue.register(1, 1)

        assert not event.is_set()
        queue.acknowledge(1, "node_a")
        assert event.is_set()

    def test_is_confirmed_after_timeout(self):
        queue = AckQueue()
        queue.set_nodes_required(1)
        queue.register(1, 1)

        queue.acknowledge(1, "node_a")
        assert queue.is_confirmed(1)

    def test_is_confirmed_unknown_returns_true(self):
        queue = AckQueue()
        assert queue.is_confirmed(999)


class TestNotifyFollowers:
    @patch("backend.apps.cluster.models.sync_log.DjangoSyncLog.objects")
    @patch("backend.apps.cluster.models.sync_state.DjangoSyncState.objects")
    @patch("backend.apps.cluster.services.proxy.get_follower_proxy")
    def test_notify_followers_with_urls(self, mock_get_proxy, mock_state_manager, mock_log_manager):
        from backend.apps.cluster.middleware.write_sync import SyncWriteMiddleware

        mock_log = MagicMock()
        mock_log.id = 1
        mock_log.table_name = "tournament"
        mock_log.record_id = "abc"
        mock_log_manager.get.return_value = mock_log

        mock_state_1 = MagicMock()
        mock_state_1.url = "http://192.168.1.10:8000"
        mock_state_2 = MagicMock()
        mock_state_2.url = "http://192.168.1.11:8000"
        mock_state_manager.exclude.return_value.exclude.return_value = [mock_state_1, mock_state_2]

        mock_proxy = MagicMock()
        mock_get_proxy.return_value = mock_proxy

        middleware = SyncWriteMiddleware(lambda r: None)
        middleware.mode = "cluster"
        middleware.is_master = True

        middleware._notify_followers(1)

        time.sleep(0.2)

        mock_proxy.broadcast_sync.assert_called_once()

    @patch("backend.apps.cluster.models.sync_log.DjangoSyncLog.objects")
    @patch("backend.apps.cluster.models.sync_state.DjangoSyncState.objects")
    def test_notify_followers_skips_if_no_urls(self, mock_state_manager, mock_log_manager):
        from backend.apps.cluster.middleware.write_sync import SyncWriteMiddleware

        mock_log = MagicMock()
        mock_log.id = 1
        mock_log.table_name = "tournament"
        mock_log.record_id = "abc"
        mock_log_manager.get.return_value = mock_log

        mock_state_manager.exclude.return_value.exclude.return_value = []

        middleware = SyncWriteMiddleware(lambda r: None)
        middleware.mode = "cluster"
        middleware.is_master = True

        middleware._notify_followers(1)
        time.sleep(0.1)

    def test_exempt_path(self):
        from backend.apps.cluster.middleware.write_sync import SyncWriteMiddleware

        middleware = SyncWriteMiddleware(lambda r: None)
        assert middleware._is_exempt_path("/api/cluster/status/") is True
        assert middleware._is_exempt_path("/api/tournaments/") is False

    def test_follower_write_returns_503(self):
        from backend.apps.cluster.middleware.write_sync import SyncWriteMiddleware
        from django.test import RequestFactory

        middleware = SyncWriteMiddleware(lambda r: None)
        middleware.mode = "cluster"
        middleware.is_master = False

        factory = RequestFactory()
        request = factory.post("/api/tournaments/")
        result = middleware._handle_follower_write(request)

        assert result.status_code == 503
