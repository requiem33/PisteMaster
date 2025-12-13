from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Optional


@dataclass
class EliminationType:
    """淘汰赛类型"""
    type_code: str = field(metadata={"max_length": 30, "description": "类型代码"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    display_name: Optional[str] = field(default=None, metadata={"max_length": 50, "description": "显示名称"})
