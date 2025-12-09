from dataclasses import dataclass, field
from typing import Dict, Any, ClassVar, Optional

from core.models.enums import WeaponType


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
