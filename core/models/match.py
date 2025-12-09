from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from core.models.enums import MatchStatus, MatchResult


@dataclass
class BaseMatch:
    """对阵基类"""
    # ========== 非默认字段（必须放在前面）==========
    fencer_a_id: int  # 选手A ID
    fencer_b_id: int  # 选手B ID
    stage_id: int  # 所属阶段ID

    # ========== 带默认值的字段（必须放在后面）==========
    # 时间与场地
    scheduled_time: Optional[datetime] = None
    piste_number: Optional[int] = None  # 剑道号

    # 状态与结果
    status: MatchStatus = MatchStatus.SCHEDULED
    score_a: int = 0  # 选手A得分
    score_b: int = 0  # 选手B得分

    # 击剑特定数据
    priority: Optional[str] = None  # 优先权（花剑、佩剑）
    double_hit: bool = False  # 是否双中

    # 系统字段
    id: Optional[int] = field(default=None, compare=False)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    @property
    def winner_id(self) -> Optional[int]:
        """获取胜者ID（如果有）"""
        if self.status != MatchStatus.COMPLETED:
            return None
        if self.score_a > self.score_b:
            return self.fencer_a_id
        elif self.score_b > self.score_a:
            return self.fencer_b_id
        return None  # 平局或无胜者

    @property
    def result_from_a(self) -> Optional[MatchResult]:
        """从选手A视角的比赛结果"""
        if self.status != MatchStatus.COMPLETED:
            return None
        if self.score_a > self.score_b:
            return MatchResult.WIN
        elif self.score_b > self.score_a:
            return MatchResult.LOSS
        elif self.score_a == self.score_b:
            return MatchResult.DRAW
        return None


@dataclass
class PoolMatch(BaseMatch):
    """小组赛对阵"""
    pool_round: int = 1  # 小组内轮次
    is_for_placement: bool = False  # 是否为排位赛（如决定小组第3、4名）


@dataclass
class DirectEliminationMatch(BaseMatch):
    """淘汰赛对阵"""
    bracket_position: str = field(default="")  # 使用 field 明确标识

    # 其他淘汰赛特有字段（都必须带默认值）
    round_number: int = 1
    next_match_id: Optional[int] = None
    is_bronze_match: bool = False
