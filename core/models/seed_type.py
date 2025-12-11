from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class SeedType:
    """3.6. Seed_Type（种子类型）"""
    type_code: str = field(
        metadata={"max_length": 30, "description": "类型代码 (UNIQUE)", "constraint": "UNIQUE, NOT NULL"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    display_name: Optional[str] = field(default=None, metadata={"max_length": 50, "description": "显示名称"})
