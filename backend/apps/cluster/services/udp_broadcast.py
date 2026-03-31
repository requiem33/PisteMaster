import asyncio
import logging
import socket
import time
from typing import Callable, Optional, Dict

from backend.apps.cluster.schemas.messages import (
    BaseMessage,
    parse_message,
    MessageType,
)

logger = logging.getLogger(__name__)


class UDPBroadcastService:
    DEFAULT_PORT = 9000
    BUFFER_SIZE = 8192
    RETRY_COUNT = 2
    RETRY_DELAY_MS = 500

    def __init__(
        self,
        port: int = DEFAULT_PORT,
        node_id: str = "",
        on_message: Optional[Callable[[BaseMessage, str], None]] = None,
    ):
        self.port = port
        self.node_id = node_id
        self.on_message = on_message
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.receive_task: Optional[asyncio.Task] = None
        self.seq_num = 0
        self._seen_messages: Dict[str, float] = {}
        self._seen_messages_ttl = 60.0

    def _get_seq_num(self) -> int:
        self.seq_num += 1
        return self.seq_num

    def _is_duplicate(self, msg: BaseMessage) -> bool:
        key = f"{msg.node_id}:{msg.seq_num}:{msg.type.value}"
        now = time.time()
        self._cleanup_seen_messages(now)
        if key in self._seen_messages:
            return True
        self._seen_messages[key] = now
        return False

    def _cleanup_seen_messages(self, now: float) -> None:
        expired_keys = [k for k, v in self._seen_messages.items() if now - v > self._seen_messages_ttl]
        for key in expired_keys:
            del self._seen_messages[key]

    def start(self) -> None:
        if self.socket is not None:
            return

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.socket.bind(("0.0.0.0", self.port))
            self.socket.setblocking(False)
            self.running = True
            logger.info(f"UDP broadcast service started on port {self.port}")
        except OSError as e:
            logger.error(f"Failed to start UDP service: {e}")
            self.socket.close()
            self.socket = None
            raise

    def stop(self) -> None:
        self.running = False
        if self.receive_task:
            self.receive_task.cancel()
            self.receive_task = None
        if self.socket:
            self.socket.close()
            self.socket = None
        logger.info("UDP broadcast service stopped")

    async def receive_loop(self) -> None:
        if not self.socket:
            raise RuntimeError("UDP service not started")

        loop = asyncio.get_event_loop()

        while self.running:
            try:
                data, addr = await loop.sock_recvfrom(self.socket, self.BUFFER_SIZE)
                if not data:
                    continue

                try:
                    msg = parse_message(data)
                    if self._is_duplicate(msg):
                        continue

                    if msg.node_id == self.node_id:
                        continue

                    if self.on_message:
                        self.on_message(msg, addr[0])

                except Exception as e:
                    logger.warning(f"Failed to parse message from {addr}: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in receive loop: {e}")

    def broadcast(self, message: BaseMessage) -> None:
        if not self.socket:
            raise RuntimeError("UDP service not started")

        if not hasattr(message, "seq_num") or message.seq_num == 1:
            message.seq_num = self._get_seq_num()

        data = message.to_json().encode("utf-8")

        broadcast_addr = "255.255.255.255"

        for attempt in range(self.RETRY_COUNT):
            try:
                self.socket.sendto(data, (broadcast_addr, self.port))
                if attempt == 0:
                    logger.debug(f"Broadcast {message.type.value} (seq={message.seq_num})")
            except Exception as e:
                logger.error(f"Failed to send broadcast (attempt {attempt + 1}): {e}")
                if attempt < self.RETRY_COUNT - 1:
                    time.sleep(self.RETRY_DELAY_MS / 1000.0)
                else:
                    raise

            if attempt < self.RETRY_COUNT - 1 and message.type in (
                MessageType.MASTER_ANNOUNCE,
                MessageType.GOODBYE,
            ):
                time.sleep(self.RETRY_DELAY_MS / 1000.0)

    async def broadcast_async(self, message: BaseMessage) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.broadcast, message)

    def send_to(self, message: BaseMessage, host: str) -> None:
        if not self.socket:
            raise RuntimeError("UDP service not started")

        if not hasattr(message, "seq_num") or message.seq_num == 1:
            message.seq_num = self._get_seq_num()

        data = message.to_json().encode("utf-8")

        try:
            self.socket.sendto(data, (host, self.port))
            logger.debug(f"Sent {message.type.value} to {host}")
        except Exception as e:
            logger.error(f"Failed to send message to {host}: {e}")
            raise

    async def send_to_async(self, message: BaseMessage, host: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.send_to, message, host)

    def get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"
