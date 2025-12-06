# core/models/competition.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, ClassVar, List
from .enums import WeaponType, GenderCategory, AgeGroup, EventType


@dataclass
class CompetitionRules:
    """比赛规则配置"""
    name: str
    weapon_type: WeaponType
    is_default: bool = False  # 是否为系统默认规则

    # 可配置的规则参数
    config: Dict[str, Any] = field(default_factory=lambda: {
        'pool_size': 7,  # 小组赛人数
        'promotion_count': 4,  # 小组晋级人数
        'match_duration': 180,  # 单场比赛时长（秒）
        'double_hit_rule': 'priority',  # 双中规则: priority/同时无效
        'required_hits': 5,  # 所需击中剑数
    })

    # 类变量：存储默认规则实例
    _default_rules: ClassVar[Dict[str, 'CompetitionRules']] = {}

    def __post_init__(self):
        """初始化后，如果是默认规则则注册"""
        if self.is_default:
            key = f"{self.weapon_type.value}_{self.name}"
            self._default_rules[key] = self

    @classmethod
    def get_default_for_weapon(cls, weapon_type: WeaponType) -> Optional['CompetitionRules']:
        """获取某武器的默认规则"""
        for rule in cls._default_rules.values():
            if rule.weapon_type == weapon_type and rule.is_default:
                return rule
        return None

    def validate_match(self, score_a: int, score_b: int) -> bool:
        """验证比赛得分是否符合规则（示例）"""
        max_score = self.config.get('required_hits', 5)
        return score_a <= max_score and score_b <= max_score


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


@dataclass
class TournamentEvent:
    """赛事单元：个人赛或团体赛"""
    name: str  # 如 "个人赛", "团体赛"
    type: EventType
    items: List[CompetitionItem] = field(default_factory=list)

    def add_item(self, item: CompetitionItem) -> None:
        """添加比赛单项"""
        # 验证类型一致性：个人赛只能包含个人项目等
        if (self.type == EventType.INDIVIDUAL and item.team_ids) or \
                (self.type == EventType.TEAM and item.participant_ids):
            raise ValueError(f"比赛单项类型与{self.type.value}类型不匹配")
        self.items.append(item)