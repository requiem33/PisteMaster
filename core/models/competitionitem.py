from dataclasses import dataclass, field
from typing import List, Optional

from core.models.enums import WeaponType, GenderCategory, AgeGroup, StageStatus
from core.models.tournamentevent import CompetitionStatus
from core.models.rule import CompetitionRules
from core.models.stage import CompetitionStage


@dataclass
class CompetitionItem:
    """比赛单项：如'男子花剑个人（成年组）'"""
    name: str  # 显示名称，如 "男子花剑个人（成年组）"
    weapon_type: WeaponType
    gender_category: GenderCategory
    age_group: AgeGroup

    # 使用的规则
    rules: CompetitionRules

    # 参赛选手/队伍ID列表
    participant_ids: List[int] = field(default_factory=list)  # 个人赛：选手ID
    team_ids: List[int] = field(default_factory=list)  # 团体赛：队伍ID

    status: CompetitionStatus = CompetitionStatus.DRAFT
    stages: List[CompetitionStage] = field(default_factory=list)

    @property
    def is_individual(self) -> bool:
        """是否为个人赛（通过participant_ids判断）"""
        return len(self.participant_ids) > 0

    def add_participant(self, fencer_id: int) -> bool:
        """添加选手到个人赛"""
        if fencer_id not in self.participant_ids:
            self.participant_ids.append(fencer_id)
            return True
        return False

    def add_team(self, team_id: int) -> bool:
        """添加队伍到团体赛"""
        if team_id not in self.team_ids:
            self.team_ids.append(team_id)
            return True
        return False

    def can_change_status(self, new_status: CompetitionStatus) -> tuple[bool, str]:
        """检查是否可以变更到目标状态，返回 (是否允许, 原因)"""
        # 定义允许的状态流转路径
        allowed_transitions = {
            CompetitionStatus.DRAFT: [CompetitionStatus.OPEN, CompetitionStatus.CANCELLED],
            CompetitionStatus.OPEN: [CompetitionStatus.CLOSED, CompetitionStatus.CANCELLED],
            CompetitionStatus.CLOSED: [CompetitionStatus.ONGOING, CompetitionStatus.CANCELLED],
            CompetitionStatus.ONGOING: [CompetitionStatus.COMPLETED],
            CompetitionStatus.COMPLETED: [],
            CompetitionStatus.CANCELLED: [],
        }

        if new_status not in allowed_transitions.get(self.status, []):
            return False, f"不允许从 {self.status.value} 变更为 {new_status.value}"

        # 可以添加更多业务规则，例如：
        if new_status == CompetitionStatus.OPEN and not self.rules:
            return False, "无法开启报名：未设置比赛规则"
        if new_status == CompetitionStatus.CLOSED and len(self.participant_ids) < 2:
            return False, "至少需要2名选手才能截止报名"

        return True, ""

    def change_status(self, new_status: CompetitionStatus) -> bool:
        """变更状态（执行业务规则验证）"""
        can_change, reason = self.can_change_status(new_status)
        if not can_change:
            # 在实际项目中，这里可以记录日志或抛出特定异常
            print(f"状态变更失败: {reason}")
            return False

        self.status = new_status
        return True

    def open_registration(self) -> bool:
        """开启报名（便捷方法）"""
        return self.change_status(CompetitionStatus.OPEN)

    def close_registration(self) -> bool:
        """截止报名"""
        return self.change_status(CompetitionStatus.CLOSED)

    # ========== 修改原有的报名方法，加入状态校验 ==========
    def can_add_participant(self, fencer_id: int) -> tuple[bool, str]:
        """检查是否可以添加选手（包含状态校验）"""
        if self.status != CompetitionStatus.OPEN:
            return False, f'当前状态为 {self.status.value}，无法添加选手'

        if fencer_id in self.participant_ids:
            return False, '选手已报名'

        # 其他业务规则（如人数限制等）
        return True, ''

    def add_stage(self, stage: CompetitionStage):
        """添加比赛阶段"""
        stage.competition_item_id = self.id
        self.stages.append(stage)

    def get_current_stage(self) -> Optional[CompetitionStage]:
        """获取当前进行中的阶段"""
        for stage in self.stages:
            if stage.status == StageStatus.ONGOING:
                return stage
        return None
