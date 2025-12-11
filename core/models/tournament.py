from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import date, datetime
from typing import Optional


@dataclass
class Tournament:
    """
    1.1. Tournament（赛事主表）- 修正了字段顺序以符合Python语法
    """
    # -----------------------------------------------------------
    # 必填字段 (Required / Positional Arguments)
    # 必须放在最前面，且没有 default 或 default_factory
    # -----------------------------------------------------------
    tournament_name: str = field(metadata={"max_length": 200, "description": "赛事名称"})
    start_date: date = field(metadata={"description": "开始日期"})
    end_date: date = field(metadata={"description": "结束日期"})
    status_id: UUID = field(metadata={"foreign_key": "Tournament_Status", "description": "赛事状态"})

    # -----------------------------------------------------------
    # 有默认值的字段 (Optional / Keyword-Only Arguments)
    # 必须放在必填字段的后面
    # -----------------------------------------------------------
    # 主键，有 default_factory，视为有默认值
    id: UUID = field(default_factory=uuid4, metadata={"description": "主键，全局唯一标识"})

    # 可选字段
    organizer: Optional[str] = field(default=None, metadata={"max_length": 200, "description": "主办方"})
    location: Optional[str] = field(default=None, metadata={"max_length": 200, "description": "赛事举办地"})

    # 时间戳字段
    created_at: datetime = field(default_factory=datetime.now,
                                 metadata={"description": "创建时间", "db_default": "NOW()"})
    updated_at: datetime = field(default_factory=datetime.now,
                                 metadata={"description": "更新时间", "db_default": "NOW()"})
