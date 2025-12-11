from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional


@dataclass
class Event:
    """
    1.2. Event（比赛项目）
    定义了一个赛事中的具体比赛项目（如：男子个人花剑、女子团体佩剑）。
    """
    # -----------------------------------------------------------
    # 必填字段 (Required / Positional Arguments)
    # -----------------------------------------------------------
    # FKs - 这些外键在创建项目时通常是必须确定的
    tournament_id: UUID = field(metadata={"foreign_key": "Tournament", "description": "所属赛事"})
    rule_id: UUID = field(metadata={"foreign_key": "Rule", "description": "赛制规则"})
    event_type_id: UUID = field(metadata={"foreign_key": "Event_Type", "description": "项目类型"})
    status_id: UUID = field(metadata={"foreign_key": "Event_Status", "description": "项目状态"})

    # NOT NULL 约束字段
    event_name: str = field(metadata={"max_length": 200, "description": "项目名称（如'男子个人佩剑'）"})
    is_team_event: bool = field(metadata={"description": "是否为团体赛"})

    # -----------------------------------------------------------
    # 有默认值的字段 (Optional / Keyword-Only Arguments)
    # -----------------------------------------------------------
    # 主键
    id: UUID = field(default_factory=uuid4, metadata={"description": "主键，全局唯一标识"})

    # 可选/时间戳字段
    start_time: Optional[datetime] = field(default=None, metadata={"description": "项目计划开始时间"})
    created_at: datetime = field(default_factory=datetime.now,
                                 metadata={"description": "创建时间", "db_default": "NOW()"})
    updated_at: datetime = field(default_factory=datetime.now,
                                 metadata={"description": "更新时间", "db_default": "NOW()"})
