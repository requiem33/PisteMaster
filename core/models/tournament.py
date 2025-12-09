"""
击剑赛事核心模型
遵循FIE（国际剑联）赛事标准的基本结构
"""

from typing import Dict, Any
from .base import BaseModel


class Tournament(BaseModel):
    """
    击剑赛事

    表示一个击剑比赛赛事，包含基本的赛事信息

    属性:
        name: 赛事名称，如"2024年全国击剑锦标赛"
        location: 比赛地点，如"北京国家会议中心"
    """

    def __init__(self, name: str, location: str):
        """
        初始化赛事

        参数:
            name: 赛事名称，不能为空
            location: 比赛地点，不能为空
        """
        self.name = name
        self.location = location

        # 自动验证数据
        self.validate()

    def validate(self) -> None:
        """
        验证赛事数据的有效性

        遵循FIE基本规则：
        1. 赛事名称不能为空
        2. 比赛地点不能为空
        3. 名称和地点长度在合理范围内

        抛出:
            ValueError: 当赛事数据无效时
        """
        # 检查名称
        if not self.name or not self.name.strip():
            raise ValueError("赛事名称不能为空")

        # 检查地点
        if not self.location or not self.location.strip():
            raise ValueError("比赛地点不能为空")

        # 检查名称长度（FIE标准建议）
        name_length = len(self.name.strip())
        if name_length < 2:
            raise ValueError("赛事名称过短")
        if name_length > 200:
            raise ValueError("赛事名称不能超过200个字符")

        # 检查地点长度
        location_length = len(self.location.strip())
        if location_length < 2:
            raise ValueError("比赛地点过短")
        if location_length > 100:
            raise ValueError("比赛地点不能超过100个字符")

    def to_dict(self) -> Dict[str, Any]:
        """
        将赛事转换为字典表示

        返回:
            Dict[str, Any]: 包含赛事所有属性的字典
        """
        return {
            "name": self.name,
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tournament":
        """
        从字典创建赛事对象

        参数:
            data: 包含赛事数据的字典，必须包含"name"和"location"键

        返回:
            Tournament: 新创建的赛事对象

        抛出:
            ValueError: 当字典数据无效时
        """
        # 检查必需字段
        required_fields = ["name", "location"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必需字段: {field}")

        return cls(
            name=data["name"],
            location=data["location"]
        )

    def __str__(self) -> str:
        """
        返回赛事的友好字符串表示

        返回:
            str: 赛事名称和地点的组合
        """
        return f"赛事: {self.name} @ {self.location}"

    def __repr__(self) -> str:
        """
        返回赛事的详细字符串表示，用于调试

        返回:
            str: 包含类名和属性的表示
        """
        return f"Tournament(name={repr(self.name)}, location={repr(self.location)})"

    def __eq__(self, other: Any) -> bool:
        """
        判断两个赛事是否相等

        基于名称和地点判断相等性（业务逻辑判断）
        注意：这不是数据库的主键相等，而是业务逻辑相等

        参数:
            other: 要比较的对象

        返回:
            bool: 如果名称和地点都相同则返回True
        """
        if not isinstance(other, Tournament):
            return False

        return (self.name == other.name and
                self.location == other.location)

    def __hash__(self) -> int:
        """
        返回赛事的哈希值

        用于将赛事对象放入集合或作为字典键

        返回:
            int: 基于名称和地点的哈希值
        """
        return hash((self.name, self.location))
