from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class SyncOperation(str, Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


@dataclass
class SyncLog:
    """Sync log domain model - records data changes for cluster synchronization."""

    table_name: str = field(metadata={"max_length": 100, "description": "Table/entity name"})
    record_id: str = field(metadata={"max_length": 100, "description": "Primary key of changed record"})
    operation: str = field(metadata={"description": "Operation type: INSERT, UPDATE, DELETE"})
    data: Dict[str, Any] = field(default_factory=dict, metadata={"description": "JSON data of the change"})
    version: int = field(default=1, metadata={"description": "Version number for conflict resolution"})

    id: Optional[int] = field(default=None, metadata={"description": "Auto-increment primary key"})
    created_at: datetime = field(default_factory=datetime.now, metadata={"description": "Timestamp when log was created"})

    def __post_init__(self):
        if isinstance(self.operation, SyncOperation):
            self.operation = self.operation.value
        valid_operations = [op.value for op in SyncOperation]
        if self.operation not in valid_operations:
            raise ValueError(f"Invalid operation: {self.operation}. Must be one of {valid_operations}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "operation": self.operation,
            "data": self.data,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
