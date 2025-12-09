"""
PisteMaster 核心模块

包含击剑编排系统的所有核心业务逻辑，与任何框架解耦。
这是整个系统的业务核心，应该保持纯净的业务逻辑。
"""

from . import models

__all__ = ["models"]
__version__ = "0.1.0"

# 提供方便的顶级导入
try:
    from .models import BaseModel, Tournament
except ImportError:
    # 在开发过程中可能会缺少依赖，这里静默失败
    pass