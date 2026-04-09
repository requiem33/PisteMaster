"""Unit tests for AckQueue and PendingAck — threading.Event based."""

import threading
import time
import pytest

from backend.apps.cluster.services.ack_queue import AckQueue, PendingAck


class TestPendingAck:
    def test_default_fields(self):
        ack = PendingAck(sync_log_id=1)
        assert ack.sync_log_id == 1
        assert isinstance(ack.event, threading.Event)
        assert isinstance(ack.confirmed_nodes, set)
        assert len(ack.confirmed_nodes) == 0

    def test_to_dict(self):
        ack = PendingAck(sync_log_id=42)
        ack.confirmed_nodes.add("node_a")
        d = ack.to_dict()
        assert d["sync_log_id"] == 42
        assert "node_a" in d["confirmed_nodes"]

    def test_event_initially_unset(self):
        ack = PendingAck(sync_log_id=1)
        assert not ack.event.is_set()


class TestAckQueue:
    def test_register_returns_event(self):
        queue = AckQueue()
        event = queue.register(1, replicas_required=1)
        assert isinstance(event, threading.Event)
        assert not event.is_set()

    def test_register_same_id_returns_same_event(self):
        queue = AckQueue()
        event1 = queue.register(1, replicas_required=1)
        event2 = queue.register(1, replicas_required=1)
        assert event1 is event2

    def test_acknowledge_sets_event(self):
        queue = AckQueue()
        queue.set_nodes_required(1)
        event = queue.register(1, replicas_required=1)
        assert not event.is_set()

        result = queue.acknowledge(1, "node_a")
        assert result is True
        assert event.is_set()

    def test_acknowledge_unknown_id_returns_false(self):
        queue = AckQueue()
        result = queue.acknowledge(999, "node_a")
        assert result is False

    def test_multiple_nodes_required(self):
        queue = AckQueue()
        queue.set_nodes_required(2)
        event = queue.register(1, replicas_required=2)

        queue.acknowledge(1, "node_a")
        assert not event.is_set()

        queue.acknowledge(1, "node_b")
        assert event.is_set()

    def test_duplicate_ack_same_node(self):
        queue = AckQueue()
        queue.set_nodes_required(1)
        event = queue.register(1, replicas_required=1)

        queue.acknowledge(1, "node_a")
        assert event.is_set()

        queue.acknowledge(1, "node_a")
        # Event stays set; only 1 confirmed node

    def test_is_confirmed(self):
        queue = AckQueue()
        queue.set_nodes_required(1)
        queue.register(1, replicas_required=1)

        assert not queue.is_confirmed(1)
        queue.acknowledge(1, "node_a")
        assert queue.is_confirmed(1)

    def test_is_confirmed_unknown_id_returns_true(self):
        queue = AckQueue()
        assert queue.is_confirmed(999)

    def test_get_confirmed_nodes(self):
        queue = AckQueue()
        queue.set_nodes_required(3)
        queue.register(1, replicas_required=3)

        queue.acknowledge(1, "node_a")
        queue.acknowledge(1, "node_b")

        nodes = queue.get_confirmed_nodes(1)
        assert set(nodes) == {"node_a", "node_b"}

    def test_get_confirmed_nodes_unknown_id(self):
        queue = AckQueue()
        assert queue.get_confirmed_nodes(999) == []

    def test_get_pending_count(self):
        queue = AckQueue()
        assert queue.get_pending_count() == 0
        queue.register(1)
        queue.register(2)
        assert queue.get_pending_count() == 2

        queue.acknowledge(1, "node_a")
        assert queue.get_pending_count() == 1

    def test_get_min_confirmed_id(self):
        queue = AckQueue()
        queue.set_nodes_required(1)
        queue.register(5)
        queue.register(10)

        result = queue.get_min_confirmed_id()
        assert result == 4  # min(5,10)-1

    def test_get_min_confirmed_id_empty(self):
        queue = AckQueue()
        assert queue.get_min_confirmed_id() == 0

    def test_get_pending_ids(self):
        queue = AckQueue()
        queue.register(1)
        queue.register(2)
        assert set(queue.get_pending_ids()) == {1, 2}

    def test_get_pending_details(self):
        queue = AckQueue()
        queue.register(42)
        details = queue.get_pending_details()
        assert len(details) == 1
        assert details[0]["sync_log_id"] == 42

    def test_remove(self):
        queue = AckQueue()
        queue.register(1)
        assert queue.remove(1) is True
        assert queue.remove(1) is False

    def test_clear_all(self):
        queue = AckQueue()
        queue.register(1)
        queue.register(2)
        count = queue.clear_all()
        assert count == 2
        assert queue.get_pending_count() == 0

    def test_set_nodes_required_minimum(self):
        queue = AckQueue()
        with pytest.raises(ValueError):
            queue.set_nodes_required(0)

    def test_thread_safety(self):
        """Test that concurrent register/acknowledge is thread-safe."""
        queue = AckQueue()
        queue.set_nodes_required(10)
        event = queue.register(1, replicas_required=10)

        results = []

        def acknowledge(node_id):
            result = queue.acknowledge(1, node_id)
            results.append((node_id, result))

        threads = [threading.Thread(target=acknowledge, args=(f"node_{i}",)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert event.is_set()
        assert len(results) == 10

    def test_event_wait_timeout(self):
        """Test that threading.Event.wait() respects timeout."""
        queue = AckQueue()
        queue.set_nodes_required(2)
        event = queue.register(1, replicas_required=2)

        confirmed = event.wait(timeout=0.05)
        assert not confirmed

    def test_event_wait_confirmed(self):
        """Test that event is set when required ACKs arrive."""
        queue = AckQueue()
        queue.set_nodes_required(1)
        event = queue.register(1, replicas_required=1)

        def delay_ack():
            time.sleep(0.05)
            queue.acknowledge(1, "node_a")

        threading.Thread(target=delay_ack, daemon=True).start()

        confirmed = event.wait(timeout=1.0)
        assert confirmed
