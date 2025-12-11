from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Fencer:
    """3.1. Fencer（击剑运动员）"""
    first_name: str = field(metadata={"max_length": 100, "description": "名"})
    last_name: str = field(metadata={"max_length": 100, "description": "姓"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    display_name: Optional[str] = field(default=None, metadata={"max_length": 200, "description": "显示名称（姓+名）"})
    gender: Optional[str] = field(default=None, metadata={"max_length": 10, "description": "性别"})
    country_code: Optional[str] = field(default=None, metadata={"max_length": 3, "description": "IOC 代码 (CHAR(3))"})
    birth_date: Optional[date] = field(default=None, metadata={"description": "出生日期"})
    fencing_id: Optional[str] = field(default=None, metadata={"max_length": 50, "description": "国际击剑ID (UNIQUE)",
                                                              "constraint": "UNIQUE"})
    current_ranking: Optional[int] = field(default=None, metadata={"description": "当前世界排名"})
    primary_weapon: Optional[str] = field(default=None, metadata={"max_length": 10, "description": "主剑种"})
    created_at: datetime = field(default_factory=datetime.now,
                                 metadata={"description": "创建时间", "db_default": "NOW()"})
    updated_at: datetime = field(default_factory=datetime.now,
                                 metadata={"description": "更新时间", "db_default": "NOW()"})
