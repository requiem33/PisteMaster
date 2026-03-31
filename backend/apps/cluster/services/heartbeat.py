import asyncio
import logging
import time
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class HeartbeatMonitor:
    HEARTBEAT_INTERVAL = 5.0
    HEARTBEAT_TIMEOUT = 15.0
    RETRANSMIT_COUNT = 2
    RETRANSMIT_DELAY_MS = 500

    def __init__(
        self,
        node_id: str,
        udp_service,
        on_timeout: Optional[Callable[[], None]] = None,
        get_last_sync_id: Optional[Callable[[], int]] = None,
    ):
        self.node_id = node_id
        self.udp_service = udp_service
        self.on_timeout = on_timeout
        self.get_last_sync_id = get_last_sync_id or (lambda: 0)

        self.last_heartbeat_time: float = 0
        self.master_id: Optional[str] = None
        self.running = False
        self.is_master = False

        self._heartbeat_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None

    def set_master(self, is_master: bool, master_id: Optional[str] = None) -> None:
        self.is_master = is_master
        if master_id:
            self.master_id = master_id

        if is_master:
            self.last_heartbeat_time = time.time()
        else:
            self.last_heartbeat_time = 0

    def record_heartbeat(self, master_id: str) -> None:
        self.master_id = master_id
        self.last_heartbeat_time = time.time()
        logger.debug(f"Heartbeat received from master: {master_id}")

    def check_timeout(self) -> bool:
        if not self.master_id or self.is_master:
            return False

        elapsed = time.time() - self.last_heartbeat_time
        if elapsed > self.HEARTBEAT_TIMEOUT:
            logger.warning(f"Heartbeat timeout: {elapsed:.1f}s since last heartbeat " f"from master {self.master_id}")
            return True
        return False

    async def start(self) -> None:
        self.running = True

        if self.is_master:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        else:
            self._monitor_task = asyncio.create_task(self._monitor_loop())

    def stop(self) -> None:
        self.running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None

    async def _heartbeat_loop(self) -> None:
        from backend.apps.cluster.schemas.messages import HeartbeatMessage

        while self.running:
            try:
                last_sync_id = self.get_last_sync_id()

                msg = HeartbeatMessage(
                    node_id=self.node_id,
                    timestamp=int(time.time()),
                    last_sync_id=last_sync_id,
                )

                for attempt in range(self.RETRANSMIT_COUNT):
                    await self.udp_service.broadcast_async(msg)
                    if attempt < self.RETRANSMIT_COUNT - 1:
                        await asyncio.sleep(self.RETRANSMIT_DELAY_MS / 1000.0)

                logger.debug(f"Heartbeat sent (seq={msg.seq_num}, " f"last_sync_id={last_sync_id})")

                await asyncio.sleep(self.HEARTBEAT_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
                await asyncio.sleep(1.0)

    async def _monitor_loop(self) -> None:
        while self.running:
            try:
                if self.master_id and self.check_timeout():
                    if self.on_timeout:
                        logger.info(f"Triggering election due to heartbeat timeout " f"(master={self.master_id})")
                        self.on_timeout()

                await asyncio.sleep(1.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(1.0)

    def get_time_since_last_heartbeat(self) -> float:
        if not self.master_id:
            return 0
        return time.time() - self.last_heartbeat_time

    def is_healthy(self) -> bool:
        if self.is_master:
            return True
        if not self.master_id:
            return False
        return not self.check_timeout()
