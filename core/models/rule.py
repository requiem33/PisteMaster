from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Optional
from decimal import Decimal


@dataclass
class Rule:
    """
    1.3. Rule（赛制规则）
    定义一个比赛项目所遵循的全部赛制规则。
    """
    # -----------------------------------------------------------
    # 必填字段 (Required / Positional Arguments)
    # -----------------------------------------------------------
    rule_name: str = field(metadata={"max_length": 100, "description": "规则名称"})
    total_qualified_count: int = field(metadata={"description": "小组赛后总晋级人数"})

    # 外键 (FKs)
    elimination_type_id: UUID = field(
        metadata={"foreign_key": "Elimination_Type", "description": "淘汰赛类型 (如单败淘汰)"})
    final_ranking_type_id: UUID = field(
        metadata={"foreign_key": "Ranking_Type", "description": "名次决出方式 (如是否有铜牌赛)"})

    # -----------------------------------------------------------
    # 有默认值的字段 (Optional / Keyword-Only Arguments)
    # -----------------------------------------------------------
    # 主键
    id: UUID = field(default_factory=uuid4, metadata={"description": "主键，全局唯一标识"})

    # 可选字段 (Nullable)
    match_format: Optional[str] = field(default=None, metadata={"max_length": 50,
                                                                "description": "单场比赛格式 (如 3x3 min / 1x5 min)"})
    pool_size: Optional[int] = field(default=None,
                                     metadata={"db_constraint": "CHECK (>=3)", "description": "小组赛每组人数"})
    match_duration: Optional[int] = field(default=None, metadata={"description": "单局时长（秒）"})
    match_score_pool: Optional[int] = field(default=None, metadata={"description": "小组赛目标分数"})
    match_score_elimination: Optional[int] = field(default=None, metadata={"description": "淘汰赛目标分数"})
    group_qualification_ratio: Optional[Decimal] = field(default=None, metadata={"decimal_precision": (5, 4),
                                                                                 "description": "晋级比例（备用）"})
    description: Optional[str] = field(default=None, metadata={"description": "规则描述"})
