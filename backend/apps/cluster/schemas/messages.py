from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any
import json


class MessageType(Enum):
    ANNOUNCE = "announce"
    HEARTBEAT = "heartbeat"
    MASTER_ANNOUNCE = "master_announce"
    GOODBYE = "goodbye"
    SYNC_REQUEST = "sync_request"
    ACK = "ack"


@dataclass
class BaseMessage:
    type: MessageType = MessageType.ANNOUNCE
    node_id: str = ""
    timestamp: int = 0
    seq_num: int = 1
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["type"] = self.type.value
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseMessage":
        raise NotImplementedError


@dataclass
class AnnounceMessage(BaseMessage):
    ip: str = ""
    port: int = 8000
    is_master: bool = False

    def __post_init__(self):
        self.type = MessageType.ANNOUNCE

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnnounceMessage":
        return cls(
            type=MessageType.ANNOUNCE,
            node_id=data["node_id"],
            timestamp=data["timestamp"],
            seq_num=data.get("seq_num", 1),
            version=data.get("version", 1),
            ip=data["ip"],
            port=data.get("port", 8000),
            is_master=data.get("is_master", False),
        )


@dataclass
class HeartbeatMessage(BaseMessage):
    last_sync_id: int = 0

    def __post_init__(self):
        self.type = MessageType.HEARTBEAT

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HeartbeatMessage":
        return cls(
            type=MessageType.HEARTBEAT,
            node_id=data["node_id"],
            timestamp=data["timestamp"],
            seq_num=data.get("seq_num", 1),
            version=data.get("version", 1),
            last_sync_id=data.get("last_sync_id", 0),
        )


@dataclass
class MasterAnnounceMessage(BaseMessage):
    ip: str = ""
    port: int = 8000

    def __post_init__(self):
        self.type = MessageType.MASTER_ANNOUNCE

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MasterAnnounceMessage":
        return cls(
            type=MessageType.MASTER_ANNOUNCE,
            node_id=data["node_id"],
            timestamp=data["timestamp"],
            seq_num=data.get("seq_num", 1),
            version=data.get("version", 1),
            ip=data["ip"],
            port=data.get("port", 8000),
        )


@dataclass
class GoodbyeMessage(BaseMessage):
    reason: str = "shutdown"

    def __post_init__(self):
        self.type = MessageType.GOODBYE

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoodbyeMessage":
        return cls(
            type=MessageType.GOODBYE,
            node_id=data["node_id"],
            timestamp=data["timestamp"],
            seq_num=data.get("seq_num", 1),
            version=data.get("version", 1),
            reason=data.get("reason", "shutdown"),
        )


@dataclass
class SyncRequestMessage(BaseMessage):
    last_sync_id: int = 0
    limit: int = 100

    def __post_init__(self):
        self.type = MessageType.SYNC_REQUEST

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncRequestMessage":
        return cls(
            type=MessageType.SYNC_REQUEST,
            node_id=data["node_id"],
            timestamp=data["timestamp"],
            seq_num=data.get("seq_num", 1),
            version=data.get("version", 1),
            last_sync_id=data.get("last_sync_id", 0),
            limit=data.get("limit", 100),
        )


@dataclass
class AckMessage(BaseMessage):
    sync_id: int = 0

    def __post_init__(self):
        self.type = MessageType.ACK

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AckMessage":
        return cls(
            type=MessageType.ACK,
            node_id=data["node_id"],
            timestamp=data["timestamp"],
            seq_num=data.get("seq_num", 1),
            version=data.get("version", 1),
            sync_id=data["sync_id"],
        )


def parse_message(data: bytes) -> BaseMessage:
    parsed = json.loads(data.decode("utf-8"))
    msg_type = parsed.get("type")

    message_classes = {
        MessageType.ANNOUNCE: AnnounceMessage,
        MessageType.HEARTBEAT: HeartbeatMessage,
        MessageType.MASTER_ANNOUNCE: MasterAnnounceMessage,
        MessageType.GOODBYE: GoodbyeMessage,
        MessageType.SYNC_REQUEST: SyncRequestMessage,
        MessageType.ACK: AckMessage,
    }

    for key, value in parsed.items():
        if key == "type":
            continue
        if key in message_classes:
            msg_type = MessageType(value)
            break

    if msg_type in message_classes:
        return message_classes[msg_type].from_dict(parsed)

    raise ValueError(f"Unknown message type: {msg_type}")
