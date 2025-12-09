"""
击剑选手核心模型
表示参加击剑比赛的选手，包含基本的身份信息
"""

from typing import Dict, Any, Optional
from datetime import date, datetime
from .base import BaseModel


class Fencer(BaseModel):
    """
    击剑选手

    表示一个击剑选手，包含身份信息和基本属性

    属性:
        last_name: 姓氏（拉丁字母或本地语言）
        first_name: 名字（拉丁字母或本地语言）
        nationality: 国籍，使用ISO 3166-1 alpha-3三字母代码
        birth_date: 出生日期，用于计算年龄组和验证参赛资格
    """

    def __init__(
            self,
            last_name: str,
            first_name: str,
            nationality: str,
            birth_date: date
    ):
        """
        初始化击剑选手

        参数:
            last_name: 姓氏，不能为空
            first_name: 名字，不能为空
            nationality: 国籍三字母代码，如"CHN"、"USA"、"FRA"
            birth_date: 出生日期，date对象
        """
        self.last_name = last_name
        self.first_name = first_name
        self.nationality = nationality
        self.birth_date = birth_date

        # 自动验证数据
        self.validate()

    def validate(self) -> None:
        """
        验证选手数据的有效性

        遵循FIE（国际剑联）基本规则：
        1. 姓名不能为空
        2. 国籍必须是有效的三字母代码
        3. 出生日期必须在合理范围内（1900年至今）
        4. 选手年龄必须合理（参加比赛的最小年龄）

        抛出:
            ValueError: 当选手数据无效时
        """
        # 检查姓氏
        if not self.last_name or not self.last_name.strip():
            raise ValueError("姓氏不能为空")

        if len(self.last_name.strip()) > 50:
            raise ValueError("姓氏不能超过50个字符")

        # 检查名字
        if not self.first_name or not self.first_name.strip():
            raise ValueError("名字不能为空")

        if len(self.first_name.strip()) > 50:
            raise ValueError("名字不能超过50个字符")

        # 检查国籍
        self._validate_nationality()

        # 检查出生日期
        self._validate_birth_date()

    def _validate_nationality(self) -> None:
        """验证国籍代码"""
        if not self.nationality or not self.nationality.strip():
            raise ValueError("国籍不能为空")

        nationality = self.nationality.strip().upper()

        # 必须是3个字母
        if len(nationality) != 3:
            raise ValueError("国籍必须是3个字母的ISO代码")

        # 必须全部是大写字母
        if not nationality.isalpha():
            raise ValueError("国籍代码只能包含字母")

        if not nationality.isupper():
            raise ValueError("国籍代码必须是大写字母")

        # 更新为标准格式
        self.nationality = nationality

    def _validate_birth_date(self) -> None:
        """验证出生日期"""
        if not isinstance(self.birth_date, date):
            raise ValueError("出生日期必须是date对象")

        # 检查日期是否合理（1900年至今）
        today = date.today()

        # 不能晚于今天
        if self.birth_date > today:
            raise ValueError("出生日期不能晚于今天")

        # 不能早于1900年（合理的击剑选手年龄）
        if self.birth_date.year < 1900:
            raise ValueError("出生日期不能早于1900年")

        # 必须至少4岁（最小击剑年龄）
        age = today.year - self.birth_date.year
        if age < 4:
            raise ValueError("选手年龄太小，不符合击剑比赛要求")

        # 不能超过120岁
        if age > 120:
            raise ValueError("选手年龄太大，不符合实际情况")

    def get_age(self, reference_date: Optional[date] = None) -> int:
        """
        计算选手在参考日期的年龄

        参数:
            reference_date: 参考日期，默认为今天

        返回:
            int: 选手年龄
        """
        if reference_date is None:
            reference_date = date.today()

        age = reference_date.year - self.birth_date.year

        # 如果今年生日还没过，减1岁
        if (reference_date.month, reference_date.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1

        return age

    def get_age_group(self, reference_date: Optional[date] = None) -> str:
        """
        获取选手的年龄组

        根据FIE标准年龄组划分：
        - U10: 10岁以下
        - U12: 10-11岁
        - U14: 12-13岁
        - U16: 14-15岁
        - U20: 16-19岁
        - Senior: 20-39岁
        - Veteran: 40岁以上

        参数:
            reference_date: 参考日期，默认为今天

        返回:
            str: 年龄组代码
        """
        age = self.get_age(reference_date)

        if age < 10:
            return "U10"
        elif age < 12:
            return "U12"
        elif age < 14:
            return "U14"
        elif age < 16:
            return "U16"
        elif age < 20:
            return "U20"
        elif age < 40:
            return "Senior"
        else:
            return "Veteran"

    def get_full_name(self, western_order: bool = False) -> str:
        """
        获取选手全名

        参数:
            western_order: 是否使用西方顺序（名在前，姓在后）
                         True: "John Doe", False: "Doe John"（默认）

        返回:
            str: 全名
        """
        if western_order:
            return f"{self.first_name} {self.last_name}"
        else:
            return f"{self.last_name} {self.first_name}"

    def to_dict(self) -> Dict[str, Any]:
        """
        将选手转换为字典表示

        返回:
            Dict[str, Any]: 包含选手所有属性的字典
        """
        return {
            "last_name": self.last_name,
            "first_name": self.first_name,
            "nationality": self.nationality,
            "birth_date": self.birth_date.isoformat(),  # ISO格式字符串
            "age": self.get_age(),
            "age_group": self.get_age_group(),
            "full_name": self.get_full_name(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Fencer":
        """
        从字典创建选手对象

        参数:
            data: 包含选手数据的字典

        返回:
            Fencer: 新创建的选手对象

        抛出:
            ValueError: 当字典数据无效时
        """
        # 检查必需字段
        required_fields = ["last_name", "first_name", "nationality", "birth_date"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必需字段: {field}")

        # 解析出生日期
        birth_date = cls._parse_date(data["birth_date"])

        return cls(
            last_name=data["last_name"],
            first_name=data["first_name"],
            nationality=data["nationality"],
            birth_date=birth_date
        )

    @staticmethod
    def _parse_date(date_str: str) -> date:
        """
        解析日期字符串

        支持多种格式：
        - YYYY-MM-DD（ISO格式）
        - YYYY/MM/DD
        - DD/MM/YYYY（欧洲格式）

        参数:
            date_str: 日期字符串

        返回:
            date: 解析后的日期对象

        抛出:
            ValueError: 当日期格式无效时
        """
        date_str = str(date_str).strip()

        # 尝试多种格式
        formats = [
            "%Y-%m-%d",  # ISO格式
            "%Y/%m/%d",  # 斜杠格式
            "%d/%m/%Y",  # 欧洲格式
            "%Y.%m.%d",  # 点格式
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        raise ValueError(f"无法解析日期: {date_str}，支持的格式: YYYY-MM-DD, YYYY/MM/DD, DD/MM/YYYY")

    def __str__(self) -> str:
        """
        返回选手的友好字符串表示

        返回:
            str: 选手姓名和国籍的组合
        """
        return f"{self.get_full_name()} ({self.nationality})"

    def __repr__(self) -> str:
        """
        返回选手的详细字符串表示，用于调试

        返回:
            str: 包含类名和属性的表示
        """
        return (
            f"Fencer(last_name={repr(self.last_name)}, "
            f"first_name={repr(self.first_name)}, "
            f"nationality={repr(self.nationality)}, "
            f"birth_date={repr(self.birth_date)})"
        )

    def __eq__(self, other: Any) -> bool:
        """
        判断两个选手是否相等

        基于姓名、国籍和出生日期判断相等性
        注意：这不是数据库的主键相等，而是业务逻辑相等

        参数:
            other: 要比较的对象

        返回:
            bool: 如果所有属性都相同则返回True
        """
        if not isinstance(other, Fencer):
            return False

        return (
                self.last_name == other.last_name and
                self.first_name == other.first_name and
                self.nationality == other.nationality and
                self.birth_date == other.birth_date
        )

    def __hash__(self) -> int:
        """
        返回选手的哈希值

        用于将选手对象放入集合或作为字典键

        返回:
            int: 基于所有属性的哈希值
        """
        return hash((
            self.last_name,
            self.first_name,
            self.nationality,
            self.birth_date
        ))
