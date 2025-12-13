from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from core.models.rule import Rule


class RuleRepositoryInterface(ABC):
    """赛制规则仓库接口"""

    @abstractmethod
    def get_rule_by_id(self, rule_id: UUID) -> Optional[Rule]:
        pass

    @abstractmethod
    def get_rule_by_name(self, rule_name: str) -> Optional[Rule]:
        pass

    @abstractmethod
    def get_all_rules(self) -> List[Rule]:
        pass

    @abstractmethod
    def get_rules_by_elimination_type(self, elimination_type_id: UUID) -> List[Rule]:
        pass

    @abstractmethod
    def save_rule(self, rule: Rule) -> Rule:
        pass

    @abstractmethod
    def delete_rule(self, rule_id: UUID) -> bool:
        pass
