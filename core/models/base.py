"""
核心模型基类 - 极简版
所有core模型的基类，提供最小化接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseModel(ABC):
    """
    核心模型基类

    提供所有模型共享的基础接口，但不包含任何字段或默认实现
    子类必须实现 validate() 方法
    """

    @abstractmethod
    def validate(self) -> None:
        """
        验证模型数据的有效性

        子类必须实现此方法，用于验证模型数据是否符合业务规则
        当数据无效时应该抛出 ValueError

        抛出:
            ValueError: 当模型数据无效时
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        将模型转换为字典表示

        子类可以覆盖此方法以提供自定义的序列化逻辑
        基类提供空字典实现，鼓励子类明确实现

        返回:
            Dict[str, Any]: 模型的字典表示
        """
        return {}

    def __str__(self) -> str:
        """
        返回模型的字符串表示，用于显示和调试

        默认返回类名，子类可以覆盖以提供更有意义的信息

        返回:
            str: 模型的字符串表示
        """
        return f"{self.__class__.__name__}"

    def __repr__(self) -> str:
        """
        返回模型的官方字符串表示，用于调试

        默认返回包含类名和内存地址的信息

        返回:
            str: 模型的官方字符串表示
        """
        return f"<{self.__class__.__name__} at {hex(id(self))}>"
