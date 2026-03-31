"""
Unit tests for the BullyElection algorithm.
Tests cover election states, master/follower transitions, and edge cases.
"""

import asyncio
import pytest
from unittest.mock import MagicMock
from typing import Optional

from backend.apps.cluster.services.election import BullyElection, ElectionState
from backend.apps.cluster.services.node_discovery import NodeInfo
from backend.apps.cluster.schemas.messages import MasterAnnounceMessage


class MockUDPService:
    def __init__(self):
        self.broadcast_calls = []
        self.local_ip = "192.168.1.100"
        self.node_id = None
        self.on_message = None

    def get_local_ip(self):
        return self.local_ip

    def broadcast(self, msg):
        self.broadcast_calls.append(msg)

    async def broadcast_async(self, msg):
        self.broadcast_calls.append(msg)

    def start(self):
        pass

    def stop(self):
        pass


class MockNodeDiscovery:
    def __init__(self, node_id: str = "node_001", api_port: int = 8000):
        self.state = MagicMock()
        self.state.node_id = node_id
        self.state.is_master = False
        self.state.master_id = None
        self.state.master_ip = None
        self.state.master_port = None
        self.state.peers = {}
        self.api_port = api_port
        self.on_master_change = None
        self.on_node_join = None
        self.on_node_leave = None
        self._started = False

    def get_node_id(self) -> str:
        return self.state.node_id

    def get_peers(self):
        return list(self.state.peers.values())

    def get_master(self) -> Optional[NodeInfo]:
        if self.state.master_id and self.state.master_id in self.state.peers:
            return self.state.peers[self.state.master_id]
        return None

    def is_master(self) -> bool:
        return self.state.is_master

    def set_as_master(self):
        self.state.is_master = True
        self.state.master_id = self.state.node_id

    async def start_discovery(self):
        self._started = True

    def stop(self):
        self._started = False

    async def send_goodbye(self, reason: str = "shutdown"):
        pass


class MockHeartbeatMonitor:
    def __init__(self):
        self.is_master = False
        self.master_id = None
        self.on_timeout = None
        self.running = False

    def set_master(self, is_master: bool, master_id: Optional[str] = None):
        self.is_master = is_master
        if master_id:
            self.master_id = master_id

    async def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def record_heartbeat(self, master_id: str):
        self.master_id = master_id


@pytest.fixture
def mock_udp_service():
    return MockUDPService()


@pytest.fixture
def mock_node_discovery():
    return MockNodeDiscovery()


@pytest.fixture
def mock_heartbeat_monitor():
    return MockHeartbeatMonitor()


class TestBullyElection:
    async def test_initial_state_is_follower(self, mock_node_discovery, mock_heartbeat_monitor, mock_udp_service):
        election = BullyElection(
            node_discovery=mock_node_discovery,
            heartbeat_monitor=mock_heartbeat_monitor,
            udp_service=mock_udp_service,
        )
        assert election.state == ElectionState.FOLLOWER
        assert not election.is_master()

    async def test_single_node_becomes_master(self, mock_udp_service):
        node_discovery = MockNodeDiscovery(node_id="node_a")
        heartbeat_monitor = MockHeartbeatMonitor()

        election = BullyElection(
            node_discovery=node_discovery,
            heartbeat_monitor=heartbeat_monitor,
            udp_service=mock_udp_service,
        )

        await election._determine_initial_role()

        assert election.state == ElectionState.MASTER
        assert election.is_master()
        assert len(mock_udp_service.broadcast_calls) == 1
        assert isinstance(mock_udp_service.broadcast_calls[0], MasterAnnounceMessage)

    async def test_existing_master_becomes_follower(self, mock_udp_service):
        node_discovery = MockNodeDiscovery(node_id="node_b")
        heartbeat_monitor = MockHeartbeatMonitor()
        existing_master = NodeInfo(
            node_id="node_a",
            ip="192.168.1.101",
            port=8000,
            last_seen=1000.0,
            is_master=True,
        )
        node_discovery.state.peers = {"node_a": existing_master}
        node_discovery.state.master_id = "node_a"

        election = BullyElection(
            node_discovery=node_discovery,
            heartbeat_monitor=heartbeat_monitor,
            udp_service=mock_udp_service,
        )

        await election._determine_initial_role()

        assert election.state == ElectionState.FOLLOWER
        assert not election.is_master()

    async def test_lower_id_node_waits_for_higher_id_master(self, mock_udp_service):
        node_discovery = MockNodeDiscovery(node_id="node_a")
        heartbeat_monitor = MockHeartbeatMonitor()
        higher_peer = NodeInfo(
            node_id="node_b",
            ip="192.168.1.102",
            port=8000,
            last_seen=1000.0,
            is_master=False,
        )
        node_discovery.state.peers = {"node_b": higher_peer}

        election = BullyElection(
            node_discovery=node_discovery,
            heartbeat_monitor=heartbeat_monitor,
            udp_service=mock_udp_service,
        )
        election.ELECTION_TIMEOUT = 0.1

        await election.trigger_election()
        await asyncio.sleep(0.2)

        assert election.state == ElectionState.MASTER

    async def test_higher_id_node_intervention(self, mock_udp_service):
        node_discovery = MockNodeDiscovery(node_id="node_a")
        heartbeat_monitor = MockHeartbeatMonitor()
        higher_peer = NodeInfo(
            node_id="node_z",
            ip="192.168.1.102",
            port=8000,
            last_seen=1000.0,
            is_master=False,
        )
        node_discovery.state.peers = {"node_z": higher_peer}

        election = BullyElection(
            node_discovery=node_discovery,
            heartbeat_monitor=heartbeat_monitor,
            udp_service=mock_udp_service,
        )
        election.ELECTION_TIMEOUT = 0.5

        asyncio.create_task(election.trigger_election())

        await asyncio.sleep(0.1)
        master_peer = NodeInfo(
            node_id="node_z",
            ip="192.168.1.102",
            port=8000,
            last_seen=1000.0,
            is_master=True,
        )
        node_discovery.state.peers["node_z"] = master_peer
        node_discovery.state.master_id = "node_z"

        await asyncio.sleep(0.5)

        assert election.state == ElectionState.FOLLOWER

    async def test_on_become_master_callback(self, mock_udp_service):
        node_discovery = MockNodeDiscovery(node_id="node_001")
        heartbeat_monitor = MockHeartbeatMonitor()
        callback_called = False

        def on_become_master():
            nonlocal callback_called
            callback_called = True

        election = BullyElection(
            node_discovery=node_discovery,
            heartbeat_monitor=heartbeat_monitor,
            udp_service=mock_udp_service,
            on_become_master=on_become_master,
        )

        await election._determine_initial_role()

        assert callback_called

    async def test_on_become_follower_callback(self, mock_udp_service):
        node_discovery = MockNodeDiscovery(node_id="node_b")
        heartbeat_monitor = MockHeartbeatMonitor()
        master_info = None

        def on_become_follower(master_id: str, master_ip: str, master_port: int):
            nonlocal master_info
            master_info = (master_id, master_ip, master_port)

        existing_master = NodeInfo(
            node_id="node_a",
            ip="192.168.1.101",
            port=8000,
            last_seen=1000.0,
            is_master=True,
        )
        node_discovery.state.peers = {"node_a": existing_master}
        node_discovery.state.master_id = "node_a"

        election = BullyElection(
            node_discovery=node_discovery,
            heartbeat_monitor=heartbeat_monitor,
            udp_service=mock_udp_service,
            on_become_follower=on_become_follower,
        )

        await election._determine_initial_role()

        assert master_info == ("node_a", "192.168.1.101", 8000)

    def test_step_down(self, mock_node_discovery, mock_heartbeat_monitor, mock_udp_service):
        election = BullyElection(
            node_discovery=mock_node_discovery,
            heartbeat_monitor=mock_heartbeat_monitor,
            udp_service=mock_udp_service,
        )

        election.state = ElectionState.MASTER
        election.election_in_progress = True

        election.step_down()

        assert election.state == ElectionState.FOLLOWER
        assert not election.election_in_progress

    async def test_election_not_triggered_when_in_progress(self, mock_udp_service):
        node_discovery = MockNodeDiscovery(node_id="node_001")
        heartbeat_monitor = MockHeartbeatMonitor()

        election = BullyElection(
            node_discovery=node_discovery,
            heartbeat_monitor=heartbeat_monitor,
            udp_service=mock_udp_service,
        )

        election.election_in_progress = True

        await election.trigger_election()
        assert election.election_in_progress is True

    async def test_become_master_broadcasts_announce(self, mock_udp_service):
        node_discovery = MockNodeDiscovery(node_id="node_001")
        node_discovery.api_port = 8000
        heartbeat_monitor = MockHeartbeatMonitor()

        election = BullyElection(
            node_discovery=node_discovery,
            heartbeat_monitor=heartbeat_monitor,
            udp_service=mock_udp_service,
        )

        await election._become_master()

        assert len(mock_udp_service.broadcast_calls) == 1
        msg = mock_udp_service.broadcast_calls[0]
        assert isinstance(msg, MasterAnnounceMessage)
        assert msg.node_id == "node_001"
        assert msg.ip == mock_udp_service.local_ip
        assert msg.port == 8000

    def test_become_follower_updates_state(self, mock_udp_service):
        node_discovery = MockNodeDiscovery(node_id="node_b")
        heartbeat_monitor = MockHeartbeatMonitor()

        election = BullyElection(
            node_discovery=node_discovery,
            heartbeat_monitor=heartbeat_monitor,
            udp_service=mock_udp_service,
        )

        election.state = ElectionState.CANDIDATE
        election._become_follower("node_a", "192.168.1.100", 8000)

        assert election.state == ElectionState.FOLLOWER
        assert heartbeat_monitor.master_id == "node_a"

    async def test_stop_cancels_election_task(self, mock_udp_service):
        node_discovery = MockNodeDiscovery(node_id="node_001")
        heartbeat_monitor = MockHeartbeatMonitor()

        election = BullyElection(
            node_discovery=node_discovery,
            heartbeat_monitor=heartbeat_monitor,
            udp_service=mock_udp_service,
        )

        await election.start()
        election.stop()

        assert election._election_task is None

    async def test_multiple_peers_highest_id_becomes_master(self, mock_udp_service):
        node_discovery = MockNodeDiscovery(node_id="node_z")
        heartbeat_monitor = MockHeartbeatMonitor()
        peers = {
            "node_a": NodeInfo("node_a", "192.168.1.101", 8000, 1000.0, False),
            "node_b": NodeInfo("node_b", "192.168.1.102", 8000, 1000.0, False),
        }
        node_discovery.state.peers = peers

        election = BullyElection(
            node_discovery=node_discovery,
            heartbeat_monitor=heartbeat_monitor,
            udp_service=mock_udp_service,
        )
        election.ELECTION_TIMEOUT = 0.1

        await election.trigger_election()
        await asyncio.sleep(0.2)

        assert election.state == ElectionState.MASTER

    async def test_multiple_peers_lower_id_waits(self, mock_udp_service):
        node_discovery = MockNodeDiscovery(node_id="node_a")
        heartbeat_monitor = MockHeartbeatMonitor()
        peers = {
            "node_b": NodeInfo("node_b", "192.168.1.102", 8000, 1000.0, False),
            "node_z": NodeInfo("node_z", "192.168.1.103", 8000, 1000.0, False),
        }
        node_discovery.state.peers = peers

        election = BullyElection(
            node_discovery=node_discovery,
            heartbeat_monitor=heartbeat_monitor,
            udp_service=mock_udp_service,
        )
        election.ELECTION_TIMEOUT = 0.3

        await election.trigger_election()

        await asyncio.sleep(0.4)

        assert election.state == ElectionState.MASTER
