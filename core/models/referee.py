from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Referee:
    """7.1. Referee（裁判）"""
    first_name: str = field(metadata={"max_length": 100, "description": "名"})
    last_name: str = field(metadata={"max_length": 100, "description": "姓"})

    id: UUID = field(default_factory=uuid4, metadata={"description": "主键"})
    display_name: Optional[str] = field(default=None, metadata={"max_length": 200, "description": "显示名称"})
    country_code: Optional[str] = field(default=None, metadata={"max_length": 3, "description": "IOC 代码 (CHAR(3))"})
    license_number: Optional[str] = field(default=None, metadata={"max_length": 50, "description": "裁判证号 (UNIQUE)",
                                                                  "constraint": "UNIQUE"})
    license_level: Optional[str] = field(default=None, metadata={"max_length": 20, "description": "裁判等级"})
    is_active: bool = field(default=True, metadata={"description": "是否活跃"})
    created_at: datetime = field(default_factory=datetime.now,
                                 metadata={"description": "创建时间", "db_default": "NOW()"})
    updated_at: datetime = field(default_factory=datetime.now,
                                 metadata={"description": "更新时间", "db_default": "NOW()"})
