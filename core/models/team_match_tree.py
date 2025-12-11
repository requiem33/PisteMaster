from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass
class TeamMatchTree:
    """6.2. Team_Match_Tree（团体赛晋级树）"""
    current_match_id: UUID = field(metadata={"foreign_key": "Team_Match", "description": "当前比赛"})
    source_match_id: UUID = field(metadata={"foreign_key": "Team_Match", "description": "来源比赛"})
    source_type_id: UUID = field(metadata={"foreign_key": "Source_Type", "description": "来源类型"})

    bracket_position: Optional[str] = field(default=None, metadata={"max_length": 10, "description": "位置标识"})

    # 组合主键 (current_match_id, source_match_id) 必须在 ORM 层面处理
