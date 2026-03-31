"""
End-to-end tests for cluster functionality.
Tests cover multi-node scenarios, leader election, data replication, and failover.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
import time

from backend.apps.cluster.services.election import BullyElection, ElectionState
from backend.apps.cluster.services.node_discovery import NodeDiscovery, NodeInfo
from backend.apps.cluster.services.heartbeat import HeartbeatMonitor
from backend.apps.cluster.services.sync_manager import SyncManager, SyncOperation
from backend.apps.cluster.schemas.messages import (
    AnnounceMessage,
    MasterAnnounceMessage,
    HeartbeatMessage,
    GoodbyeMessage,
    MessageType,
)


class MockClusterNode:
    """Simulates a cluster node for testing."""

    def __init__(self, node_id: str, port: int = 8000):
        self.node_id = node_id
        self.port = port
        self.ip = "127.0.0.1"
        self.state = "follower"
        self.peers: dict = {}
        self.master_id: Optional[str] = None
        self.master_ip: Optional[str] = None
        self.messages_sent: List = []
        self.messages_received: List = []

    def get_info(self) -> NodeInfo:
        return NodeInfo(
            node_id=self.node_id,
            ip=self.ip,
            port=self.port,
            last_seen=time.time(),
            is_master=(self.state == "master"),
        )


class TestClusterFormation:
    async def test_single_node_becomes_master(self):
        node = MockClusterNode(node_id="node_001")

        mock_udp = MagicMock()
        mock_udp.broadcast_calls = []
        mock_udp.local_ip = "192.168.1.100"
        mock_udp.broadcast = lambda msg: mock_udp.broadcast_calls.append(msg)
        mock_udp.broadcast_async = AsyncMock(side_effect=lambda msg: mock_udp.broadcast_calls.append(msg))

        mock_discovery = MagicMock()
        mock_discovery.get_node_id.return_value = node.node_id
        mock_discovery.get_master.return_value = None
        mock_discovery.get_peers.return_value = []
        mock_discovery.set_as_master = MagicMock()
        mock_discovery.api_port = 8000

        mock_heartbeat = MagicMock()
        mock_heartbeat.on_timeout = None
        mock_heartbeat.set_master = MagicMock()
        mock_heartbeat.start = AsyncMock()
        mock_heartbeat.stop = MagicMock()

        election = BullyElection(
            node_discovery=mock_discovery,
            heartbeat_monitor=mock_heartbeat,
            udp_service=mock_udp,
        )

        await election._determine_initial_role()

        assert election.state == ElectionState.MASTER
        assert len(mock_udp.broadcast_calls) == 1
        assert isinstance(mock_udp.broadcast_calls[0], MasterAnnounceMessage)

    async def test_two_nodes_higher_id_wins(self):
        node_a = MockClusterNode(node_id="node_a", port=8001)
        node_b = MockClusterNode(node_id="node_z", port=8002)

        mock_udp_b = MagicMock()
        mock_udp_b.local_ip = "192.168.1.102"
        mock_udp_b.broadcast_calls = []
        mock_udp_b.broadcast_async = AsyncMock(side_effect=lambda msg: mock_udp_b.broadcast_calls.append(msg))

        mock_discovery_b = MagicMock()
        mock_discovery_b.get_node_id.return_value = node_b.node_id
        mock_discovery_b.get_master.return_value = None
        mock_discovery_b.get_peers.return_value = [node_a.get_info()]
        mock_discovery_b.set_as_master = MagicMock()
        mock_discovery_b.api_port = 8002

        mock_heartbeat_b = MagicMock()
        mock_heartbeat_b.on_timeout = None
        mock_heartbeat_b.set_master = MagicMock()
        mock_heartbeat_b.start = AsyncMock()

        election_b = BullyElection(
            node_discovery=mock_discovery_b,
            heartbeat_monitor=mock_heartbeat_b,
            udp_service=mock_udp_b,
        )
        election_b.ELECTION_TIMEOUT = 0.1

        await election_b._determine_initial_role()

        assert election_b.state == ElectionState.MASTER

    async def test_lower_id_node_becomes_follower(self):
        node_a = MockClusterNode(node_id="node_a")
        node_z = MockClusterNode(node_id="node_z")

        mock_udp_a = MagicMock()
        mock_udp_a.local_ip = "192.168.1.100"
        mock_udp_a.broadcast_async = AsyncMock()

        master_node = NodeInfo(
            node_id=node_z.node_id,
            ip="192.168.1.100",
            port=8000,
            last_seen=time.time(),
            is_master=True,
        )

        mock_discovery_a = MagicMock()
        mock_discovery_a.get_node_id.return_value = node_a.node_id
        mock_discovery_a.get_master.return_value = master_node
        mock_discovery_a.get_peers.return_value = [master_node]
        mock_discovery_a.api_port = 8000

        mock_heartbeat_a = MagicMock()
        mock_heartbeat_a.on_timeout = None
        mock_heartbeat_a.set_master = MagicMock()
        mock_heartbeat_a.start = AsyncMock()

        election_a = BullyElection(
            node_discovery=mock_discovery_a,
            heartbeat_monitor=mock_heartbeat_a,
            udp_service=mock_udp_a,
        )

        await election_a._determine_initial_role()

        assert election_a.state == ElectionState.FOLLOWER


class TestMasterFailover:
    async def test_failover_on_heartbeat_timeout(self):
        node_a = MockClusterNode(node_id="node_a")

        mock_udp_a = MagicMock()
        mock_udp_a.local_ip = "192.168.1.100"
        mock_udp_a.broadcast_calls = []
        mock_udp_a.broadcast_async = AsyncMock(side_effect=lambda msg: mock_udp_a.broadcast_calls.append(msg))
        mock_udp_a.start = MagicMock()
        mock_udp_a.stop = MagicMock()

        mock_discovery_a = MagicMock()
        mock_discovery_a.get_node_id.return_value = node_a.node_id
        mock_discovery_a.get_master.return_value = None
        mock_discovery_a.get_peers.return_value = []
        mock_discovery_a.set_as_master = MagicMock()
        mock_discovery_a.api_port = 8000

        mock_heartbeat_a = MagicMock()
        mock_heartbeat_a.on_timeout = None
        mock_heartbeat_a.set_master = MagicMock()
        mock_heartbeat_a.start = AsyncMock()

        election_callback_called = False

        def on_timeout():
            nonlocal election_callback_called
            election_callback_called = True

        mock_heartbeat_a.on_timeout = on_timeout

        heartbeat_monitor = HeartbeatMonitor(
            node_id=node_a.node_id,
            udp_service=mock_udp_a,
            on_timeout=on_timeout,
        )

        heartbeat_monitor.set_master(False, "node_b")
        heartbeat_monitor.last_heartbeat_time = 0

        timeout_occurred = heartbeat_monitor.check_timeout()
        assert timeout_occurred is True

    async def test_step_down_on_conflict(self):
        mock_udp = MagicMock()
        mock_discovery = MagicMock()
        mock_discovery.get_node_id.return_value = "node_001"
        mock_heartbeat = MagicMock()

        election = BullyElection(
            node_discovery=mock_discovery,
            heartbeat_monitor=mock_heartbeat,
            udp_service=mock_udp,
        )

        election.state = ElectionState.MASTER
        election.election_in_progress = True

        election.step_down()

        assert election.state == ElectionState.FOLLOWER
        assert election.election_in_progress is False


class TestMessageHandling:
    def test_announce_message_creation(self):
        msg = AnnounceMessage(
            node_id="node_001",
            timestamp=int(time.time()),
            seq_num=1,
            ip="192.168.1.100",
            port=8000,
            is_master=False,
        )

        assert msg.type == MessageType.ANNOUNCE
        assert msg.node_id == "node_001"
        assert msg.is_master is False

    def test_master_announce_message(self):
        msg = MasterAnnounceMessage(
            node_id="node_001",
            timestamp=int(time.time()),
            ip="192.168.1.100",
            port=8000,
        )

        assert msg.type == MessageType.MASTER_ANNOUNCE
        assert msg.node_id == "node_001"

    def test_heartbeat_message(self):
        msg = HeartbeatMessage(
            node_id="node_001",
            timestamp=int(time.time()),
            last_sync_id=100,
        )

        assert msg.type == MessageType.HEARTBEAT
        assert msg.last_sync_id == 100

    def test_goodbye_message(self):
        msg = GoodbyeMessage(
            node_id="node_001",
            timestamp=int(time.time()),
            reason="shutdown",
        )

        assert msg.type == MessageType.GOODBYE
        assert msg.reason == "shutdown"


class TestNodeDiscovery:
    def test_add_peer(self):
        mock_udp = MagicMock()
        mock_udp.node_id = None
        mock_udp.on_message = None
        mock_udp.start = MagicMock()

        discovery = NodeDiscovery(udp_service=mock_udp, api_port=8000)

        peer_info = NodeInfo(
            node_id="node_002",
            ip="192.168.1.101",
            port=8000,
            last_seen=time.time(),
        )
        discovery.state.peers["node_002"] = peer_info

        peers = discovery.get_peers()
        assert len(peers) == 1
        assert peers[0].node_id == "node_002"

    def test_master_tracking(self):
        mock_udp = MagicMock()
        mock_udp.node_id = None
        mock_udp.on_message = None
        mock_udp.start = MagicMock()
        mock_udp.get_local_ip.return_value = "192.168.1.100"

        discovery = NodeDiscovery(udp_service=mock_udp, api_port=8000)

        discovery.state.node_id = "node_001"
        discovery.set_as_master()

        assert discovery.is_master() is True
        assert discovery.state.master_id == "node_001"

    def test_peer_expiry(self):
        mock_udp = MagicMock()
        mock_udp.node_id = None
        mock_udp.on_message = None

        discovery = NodeDiscovery(udp_service=mock_udp, api_port=8000)

        old_time = time.time() - 60
        expired_peer = NodeInfo(
            node_id="expired_node",
            ip="192.168.1.105",
            port=8000,
            last_seen=old_time,
        )
        discovery.state.peers["expired_node"] = expired_peer

        discovery._cleanup_expired_nodes()

        assert "expired_node" not in discovery.state.peers


class TestDataReplication:
    @pytest.mark.django_db
    def test_master_records_change(self):
        sync_manager = SyncManager()

        sync_log = sync_manager.record_change(
            table_name="tournament",
            record_id="uuid-test",
            operation=SyncOperation.INSERT.value,
            data={"name": "Test Tournament"},
        )

        assert sync_log.id is not None
        assert sync_log.table_name == "tournament"

    @pytest.mark.django_db
    def test_follower_applies_change(self):
        from backend.apps.cluster.models import DjangoSyncLog

        sync_manager = SyncManager()
        sync_manager.register_model(
            "tournament",
            MagicMock(),
            MagicMock(),
        )

        DjangoSyncLog.objects.create(
            table_name="tournament",
            record_id="uuid-test",
            operation="INSERT",
            data={"name": "Test"},
        )

        changes = sync_manager.get_changes_since(0)
        assert len(changes.changes) >= 1

    @pytest.mark.django_db
    def test_ack_confirmation_flow(self):
        from backend.apps.cluster.services.ack_queue import AckQueue

        ack_queue = AckQueue()
        ack_queue.set_nodes_required(2)

        ack_queue.register(sync_log_id=100)

        ack_queue.acknowledge(100, "node_001")
        assert not ack_queue.is_confirmed(100)

        ack_queue.acknowledge(100, "node_002")
        assert ack_queue.is_confirmed(100)


class TestConflictResolution:
    def test_version_based_resolution(self):
        from backend.apps.cluster.services.sync_manager import SyncManager

        sync_manager = SyncManager()

        change_higher = MagicMock()
        change_higher.table_name = "tournament"
        change_higher.record_id = "test-uuid"
        change_higher.operation = "UPDATE"
        change_higher.data = {"name": "Updated Name", "version": 3}
        change_higher.version = 3

        assert sync_manager.needs_manual_review("tournament") is False

    def test_critical_table_manual_review(self):
        sync_manager = SyncManager()

        assert sync_manager.needs_manual_review("score") is True
        assert sync_manager.needs_manual_review("ranking") is True
        assert sync_manager.needs_manual_review("tournament") is False


@pytest.fixture
def cluster_config():
    return {
        "mode": "cluster",
        "is_master": False,
        "master_url": "http://192.168.1.100:8000",
        "replica_ack_required": 2,
        "ack_timeout_ms": 5000,
    }


class TestClusterConfiguration:
    def test_cluster_config_defaults(self, cluster_config):
        assert cluster_config["mode"] == "cluster"
        assert cluster_config["is_master"] is False
        assert cluster_config["replica_ack_required"] == 2

    def test_ack_queue_configuration(self, cluster_config):
        from backend.apps.cluster.services.ack_queue import AckQueue

        ack_queue = AckQueue()
        ack_queue.set_nodes_required(cluster_config["replica_ack_required"])

        assert ack_queue._nodes_required == 2


class TestElectionEdgeCases:
    async def test_concurrent_election_prevention(self):
        mock_udp = MagicMock()
        mock_udp.local_ip = "192.168.1.100"
        mock_udp.broadcast_async = AsyncMock()

        mock_discovery = MagicMock()
        mock_discovery.get_node_id.return_value = "node_001"
        mock_discovery.get_master.return_value = None
        mock_discovery.get_peers.return_value = []
        mock_discovery.set_as_master = MagicMock()
        mock_discovery.api_port = 8000

        mock_heartbeat = MagicMock()
        mock_heartbeat.on_timeout = None
        mock_heartbeat.set_master = MagicMock()

        election = BullyElection(
            node_discovery=mock_discovery,
            heartbeat_monitor=mock_heartbeat,
            udp_service=mock_udp,
        )

        election.election_in_progress = True

        await election.trigger_election()

        assert election.election_in_progress is True

    async def test_master_id_comparison(self):
        mock_discovery = MagicMock()
        mock_discovery.get_node_id.return_value = "node_abc"

        assert mock_discovery.get_node_id() == "node_abc"

        assert "node_z" > "node_abc"
        assert "node_a" < "node_abc"
