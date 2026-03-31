from datetime import datetime
from typing import Any, Dict


def versioned_fields(node_id: str = "", version: int = 1, last_modified_at: datetime = None) -> Dict[str, Any]:
    """
    Helper function to create version fields for dataclasses.

    Use this for domain models that participate in cluster synchronization:

        @dataclass
        class Tournament:
            tournament_name: str
            ...other fields...
            version: int = field(default=1)
            last_modified_node: str = field(default="")
            last_modified_at: datetime = field(default_factory=datetime.now)

    Conflict resolution uses Last-Write-Wins with these rules:
    1. Higher version wins
    2. If versions equal, higher timestamp wins
    3. If still tied, manual review required for critical data
    """
    return {
        "version": version,
        "last_modified_node": node_id,
        "last_modified_at": last_modified_at or datetime.now(),
    }
