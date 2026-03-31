import asyncio
import logging
import platform
import random

import string
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, List

from backend.apps.cluster.schemas.messages import (
    AnnounceMessage,
    MasterAnnounceMessage,
    GoodbyeMessage,
    BaseMessage,
    MessageType,
)
from backend.apps.cluster.services.udp_broadcast import UDPBroadcastService

logger = logging.getLogger(__name__)


@dataclass
class NodeInfo:
    node_id: str
    ip: str
    port: int
    last_seen: float
    is_master: bool = False

    def is_expired(self, timeout: float = 30.0) -> bool:
        return time.time() - self.last_seen > timeout


@dataclass
class ClusterState:
    node_id: str = ""
    is_master: bool = False
    master_id: Optional[str] = None
    master_ip: Optional[str] = None
    master_port: int = 8000
    peers: Dict[str, NodeInfo] = field(default_factory=dict)
    discovery_complete: bool = False
    election_in_progress: bool = False


class NodeDiscovery:
    DISCOVERY_TIMEOUT = 5.0
    NODE_EXPIRY_TIMEOUT = 30.0
    ANNOUNCE_COUNT = 3
    ANNOUNCE_INTERVAL = 1.0

    def __init__(
        self,
        udp_service: UDPBroadcastService,
        api_port: int = 8000,
        on_master_change: Optional[Callable[[str, str, int], None]] = None,
        on_node_join: Optional[Callable[[NodeInfo], None]] = None,
        on_node_leave: Optional[Callable[[str], None]] = None,
    ):
        self.udp_service = udp_service
        self.api_port = api_port
        self.on_master_change = on_master_change
        self.on_node_join = on_node_join
        self.on_node_leave = on_node_leave

        self.state = ClusterState()
        self.state.node_id = self._generate_node_id()

        self.udp_service.node_id = self.state.node_id
        self.udp_service.on_message = self._handle_message

        self._discovery_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

    def _generate_node_id(self) -> str:
        hostname = platform.node() or "node"
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"{hostname}_{suffix}"

    def _handle_message(self, message: BaseMessage, sender_ip: str) -> None:
        if message.node_id == self.state.node_id:
            return

        if message.type == MessageType.ANNOUNCE:
            self._handle_announce(message, sender_ip)
        elif message.type == MessageType.MASTER_ANNOUNCE:
            self._handle_master_announce(message, sender_ip)
        elif message.type == MessageType.GOODBYE:
            self._handle_goodbye(message, sender_ip)
        elif message.type == MessageType.HEARTBEAT:
            self._handle_heartbeat(message, sender_ip)

    def _handle_announce(self, message: AnnounceMessage, sender_ip: str) -> None:
        is_new_node = message.node_id not in self.state.peers

        self.state.peers[message.node_id] = NodeInfo(
            node_id=message.node_id,
            ip=sender_ip,
            port=message.port,
            last_seen=time.time(),
            is_master=message.is_master,
        )

        if message.is_master:
            self._update_master(message.node_id, sender_ip, message.port)

        if is_new_node and self.on_node_join:
            self.on_node_join(self.state.peers[message.node_id])

        logger.info(f"Discovered node {message.node_id} at {sender_ip}:{message.port} " f"(master={message.is_master})")

    def _handle_master_announce(self, message: MasterAnnounceMessage, sender_ip: str) -> None:
        self._update_master(message.node_id, sender_ip, message.port)

        if message.node_id in self.state.peers:
            self.state.peers[message.node_id].is_master = True
            self.state.peers[message.node_id].last_seen = time.time()

        logger.info(f"Master announced: {message.node_id} at {sender_ip}:{message.port}")

    def _handle_goodbye(self, message: GoodbyeMessage, sender_ip: str) -> None:
        if message.node_id not in self.state.peers:
            return

        del self.state.peers[message.node_id]

        if message.node_id == self.state.master_id:
            self.state.master_id = None
            self.state.master_ip = None
            logger.warning(f"Master {message.node_id} is leaving: {message.reason}")

        if self.on_node_leave:
            self.on_node_leave(message.node_id)

        logger.info(f"Node {message.node_id} left: {message.reason}")

    def _handle_heartbeat(self, message: BaseMessage, sender_ip: str) -> None:
        if message.node_id in self.state.peers:
            self.state.peers[message.node_id].last_seen = time.time()

        if message.node_id == self.state.master_id:
            self.state.master_ip = sender_ip

    def _update_master(self, master_id: str, master_ip: str, master_port: int) -> None:
        old_master = self.state.master_id
        self.state.master_id = master_id
        self.state.master_ip = master_ip
        self.state.master_port = master_port

        for node in self.state.peers.values():
            node.is_master = node.node_id == master_id

        if self.on_master_change and old_master != master_id:
            self.on_master_change(master_id, master_ip, master_port)

    async def start_discovery(self) -> None:
        self.udp_service.start()
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        await self._announce_presence()

        await asyncio.sleep(self.DISCOVERY_TIMEOUT)

        self.state.discovery_complete = True
        logger.info(f"Discovery complete. Found {len(self.state.peers)} peers: " f"{list(self.state.peers.keys())}")

    async def _announce_presence(self) -> None:
        local_ip = self.udp_service.get_local_ip()

        for i in range(self.ANNOUNCE_COUNT):
            msg = AnnounceMessage(
                node_id=self.state.node_id,
                timestamp=int(time.time()),
                seq_num=i + 1,
                ip=local_ip,
                port=self.api_port,
                is_master=self.state.is_master,
            )
            self.udp_service.broadcast(msg)
            if i < self.ANNOUNCE_COUNT - 1:
                await asyncio.sleep(self.ANNOUNCE_INTERVAL)

    async def _discovery_loop(self) -> None:
        await self.udp_service.receive_loop()

    async def _cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(10.0)
            self._cleanup_expired_nodes()

    def _cleanup_expired_nodes(self) -> None:
        expired_nodes = [node_id for node_id, node in self.state.peers.items() if node.is_expired(self.NODE_EXPIRY_TIMEOUT)]

        for node_id in expired_nodes:
            del self.state.peers[node_id]
            if self.on_node_leave:
                self.on_node_leave(node_id)
            logger.warning(f"Node {node_id} expired (no heartbeat received)")

    def stop(self) -> None:
        if self._discovery_task:
            self._discovery_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        self.udp_service.stop()

    async def send_goodbye(self, reason: str = "shutdown") -> None:
        msg = GoodbyeMessage(
            node_id=self.state.node_id,
            timestamp=int(time.time()),
            reason=reason,
        )
        await self.udp_service.broadcast_async(msg)

    def get_peers(self) -> List[NodeInfo]:
        return list(self.state.peers.values())

    def get_master(self) -> Optional[NodeInfo]:
        if self.state.master_id and self.state.master_id in self.state.peers:
            return self.state.peers[self.state.master_id]
        return None

    def is_master(self) -> bool:
        return self.state.is_master

    def set_as_master(self) -> None:
        self.state.is_master = True
        self.state.master_id = self.state.node_id
        self.state.master_ip = self.udp_service.get_local_ip()
        self.state.master_port = self.api_port

    def get_node_id(self) -> str:
        return self.state.node_id

    def compare_node_ids(self, other_id: str) -> int:
        if self.state.node_id > other_id:
            return 1
        elif self.state.node_id < other_id:
            return -1
        return 0
