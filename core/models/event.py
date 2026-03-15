from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Event:
    """
    1.2. Event（比赛项目）
    """
    # -----------------------------------------------------------
    # 必填字段
    # -----------------------------------------------------------
    tournament_id: UUID = field(metadata={"foreign_key": "Tournament", "description": "所属赛事"})
    event_name: str = field(metadata={"max_length": 200, "description": "项目名称（如'男子个人佩剑'）"})

    # -----------------------------------------------------------
    # 有默认值的字段
    # -----------------------------------------------------------
    id: UUID = field(default_factory=uuid4, metadata={"description": "主键，全局唯一标识"})
    
    rule_id: Optional[UUID] = field(default=None, metadata={"foreign_key": "Rule", "description": "赛制规则"})
    event_type: str = field(default='', metadata={"description": "项目类型(如 MEN_INDIVIDUAL_FOIL)"})
    status: str = field(default='REGISTRATION', metadata={"description": "项目状态"})
    is_team_event: bool = field(default=False, metadata={"description": "是否为团体赛"})
    current_step: int = field(default=0, metadata={"description": "当前编排步骤进度"})
    
    live_ranking: list = field(default_factory=list, metadata={"description": "实时排名快照(JSON)"})
    de_trees: Dict[str, Any] = field(default_factory=dict, metadata={"description": "各阶段淘汰赛对阵图(JSON)"})
    custom_rule_config: Dict[str, Any] = field(default_factory=dict, metadata={"description": "自定义规则配置(JSON)"})

    start_time: Optional[datetime] = field(default=None, metadata={"description": "项目计划开始时间"})
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
