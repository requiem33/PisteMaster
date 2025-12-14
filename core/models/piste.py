from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Optional


@dataclass
class Piste:
    """剑道"""
    tournament_id: UUID = field(metadata={"foreign_key": "Tournament", "description": "所属赛事"})
    piste_number: str = field(metadata={"max_length": 10, "description": "剑道编号"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    location: Optional[str] = field(default=None, metadata={"max_length": 100, "description": "具体位置"})
    piste_type: Optional[str] = field(default=None, metadata={"max_length": 20, "description": "类型"})
    is_available: bool = field(default=True, metadata={"description": "是否可用"})
    notes: Optional[str] = field(default=None, metadata={"description": "备注"})
