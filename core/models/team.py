from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Team:
    """3.2. Team（队伍）"""
    event_id: UUID = field(metadata={"foreign_key": "Event", "description": "所属项目"})
    team_name: str = field(metadata={"max_length": 200, "description": "队伍名称"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    country_code: Optional[str] = field(default=None, metadata={"max_length": 3, "description": "IOC 代码 (CHAR(3))"})
    seed_rank: Optional[int] = field(default=None, metadata={"description": "种子排名"})
    created_at: datetime = field(default_factory=datetime.now,
                                 metadata={"description": "创建时间", "db_default": "NOW()"})
