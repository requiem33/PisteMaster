from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Optional


@dataclass
class TournamentStatus:
    """
    2.1. TournamentStatus（赛事状态）
    """
    # -----------------------------------------------------------
    # 必填字段
    # -----------------------------------------------------------
    status_code: str = field(metadata={"max_length": 20, "description": "状态代码 (UNIQUE)", "constraint": "UNIQUE"})

    # -----------------------------------------------------------
    # 有默认值的字段
    # -----------------------------------------------------------
    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    display_name: Optional[str] = field(default=None, metadata={"max_length": 50, "description": "显示名称"})
    description: Optional[str] = field(default=None, metadata={"max_length": 200, "description": "描述"})
