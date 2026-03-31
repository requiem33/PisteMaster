import asyncio
import logging
import time
from enum import Enum
from typing import Optional, Callable

from backend.apps.cluster.schemas.messages import MasterAnnounceMessage
from backend.apps.cluster.services.node_discovery import NodeDiscovery
from backend.apps.cluster.services.heartbeat import HeartbeatMonitor
from backend.apps.cluster.services.udp_broadcast import UDPBroadcastService

logger = logging.getLogger(__name__)


class ElectionState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    MASTER = "master"
    ELECTING = "electing"


class BullyElection:
    ELECTION_TIMEOUT = 10.0
    MASTER_ANNOUNCE_WAIT = 2.0

    def __init__(
        self,
        node_discovery: NodeDiscovery,
        heartbeat_monitor: HeartbeatMonitor,
        udp_service: UDPBroadcastService,
        on_become_master: Optional[Callable[[], None]] = None,
        on_become_follower: Optional[Callable[[str, str, int], None]] = None,
    ):
        self.node_discovery = node_discovery
        self.heartbeat_monitor = heartbeat_monitor
        self.udp_service = udp_service
        self.on_become_master = on_become_master
        self.on_become_follower = on_become_follower

        self.state = ElectionState.FOLLOWER
        self.election_start_time: Optional[float] = None
        self.election_in_progress = False

        self._election_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        await self.node_discovery.start_discovery()
        await self._determine_initial_role()

        self.heartbeat_monitor.on_timeout = self.trigger_election
        await self.heartbeat_monitor.start()

    async def _determine_initial_role(self) -> None:
        existing_master = self.node_discovery.get_master()

        if existing_master:
            logger.info(f"Found existing master: {existing_master.node_id}")
            self.state = ElectionState.FOLLOWER
            self.heartbeat_monitor.set_master(False, existing_master.node_id)
            if self.on_become_follower:
                self.on_become_follower(
                    existing_master.node_id,
                    existing_master.ip,
                    existing_master.port,
                )
        else:
            await self.trigger_election()

    async def trigger_election(self) -> None:
        if self.election_in_progress:
            logger.debug("Election already in progress, skipping")
            return

        self.election_in_progress = True
        self.state = ElectionState.ELECTING
        self.election_start_time = time.time()

        logger.info(f"Election triggered by node {self.node_discovery.get_node_id()}")

        self._election_task = asyncio.create_task(self._run_election())

    async def _run_election(self) -> None:
        try:
            my_id = self.node_discovery.get_node_id()
            peers = self.node_discovery.get_peers()

            higher_id_nodes = [peer.node_id for peer in peers if peer.node_id > my_id]

            if not higher_id_nodes:
                logger.info(f"No nodes with higher ID than {my_id}, becoming master")
                await self._become_master()
                return

            logger.info(f"Nodes with higher ID exist: {higher_id_nodes}, " "waiting for election timeout")

            await asyncio.sleep(self.ELECTION_TIMEOUT)

            current_master = self.node_discovery.get_master()
            if current_master and current_master.is_master:
                logger.info(f"Master announced during wait: {current_master.node_id}, " "becoming follower")
                self._become_follower(current_master.node_id, current_master.ip, current_master.port)
                return

            await self._become_master()

        except asyncio.CancelledError:
            logger.debug("Election cancelled")
        except Exception as e:
            logger.error(f"Error during election: {e}")
            self.state = ElectionState.FOLLOWER
        finally:
            self.election_in_progress = False

    async def _become_master(self) -> None:
        self.state = ElectionState.MASTER
        self.node_discovery.set_as_master()

        local_ip = self.udp_service.get_local_ip()
        api_port = self.node_discovery.api_port

        msg = MasterAnnounceMessage(
            node_id=self.node_discovery.get_node_id(),
            timestamp=int(time.time()),
            ip=local_ip,
            port=api_port,
        )

        await self.udp_service.broadcast_async(msg)

        self.heartbeat_monitor.set_master(True)

        logger.info(f"Node {self.node_discovery.get_node_id()} is now MASTER " f"at {local_ip}:{api_port}")

        if self.on_become_master:
            self.on_become_master()

    def _become_follower(self, master_id: str, master_ip: str, master_port: int) -> None:
        self.state = ElectionState.FOLLOWER
        self.heartbeat_monitor.set_master(False, master_id)

        logger.info(f"Node {self.node_discovery.get_node_id()} is now FOLLOWER, " f"master is {master_id} at {master_ip}:{master_port}")

        if self.on_become_follower:
            self.on_become_follower(master_id, master_ip, master_port)

    def step_down(self) -> None:
        self.state = ElectionState.FOLLOWER

        if self.election_in_progress:
            self.election_in_progress = False

        if self._election_task:
            self._election_task.cancel()
            self._election_task = None

        self.heartbeat_monitor.set_master(False)

        logger.info(f"Node {self.node_discovery.get_node_id()} stepping down as master")

    def get_state(self) -> ElectionState:
        return self.state

    def is_master(self) -> bool:
        return self.state == ElectionState.MASTER

    def stop(self) -> None:
        if self._election_task:
            self._election_task.cancel()
            self._election_task = None
        self.heartbeat_monitor.stop()
        self.node_discovery.stop()
