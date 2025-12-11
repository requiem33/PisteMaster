from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass
class MatchTree:
    """5.3. Match_Tree（个人赛晋级树）"""
    current_match_id: UUID = field(metadata={"foreign_key": "Match", "description": "当前比赛（子节点）"})
    source_match_id: UUID = field(metadata={"foreign_key": "Match", "description": "来源比赛（父节点）"})
    source_type_id: UUID = field(metadata={"foreign_key": "Source_Type", "description": "来源类型"})

    bracket_position: Optional[str] = field(default=None,
                                            metadata={"max_length": 10, "description": "位置标识（如'W1','L1'）"})
