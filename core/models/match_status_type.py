from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Optional


@dataclass
class MatchStatusType:
    """2.3. Match_Status_Type（比赛状态）"""
    status_code: str = field(
        metadata={"max_length": 20, "description": "状态代码 (UNIQUE)", "constraint": "UNIQUE, NOT NULL"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    description: Optional[str] = field(default=None, metadata={"max_length": 100, "description": "描述"})
