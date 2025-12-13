from enum import StrEnum


class TournamentStatusCode(StrEnum):
    """赛事状态代码枚举"""
    PLANNING = "PLANNING"  # 计划中
    REGISTRATION_OPEN = "REGISTRATION_OPEN"  # 报名开放
    REGISTRATION_CLOSED = "REGISTRATION_CLOSED"  # 报名截止
    ONGOING = "ONGOING"  # 进行中
    COMPLETED = "COMPLETED"  # 已完成
    CANCELLED = "CANCELLED"  # 已取消


# 预置状态数据
PREDEFINED_STATUSES = [
    {
        "status_code": TournamentStatusCode.PLANNING,
        "display_name": "计划中",
        "description": "赛事正在计划阶段"
    },
    {
        "status_code": TournamentStatusCode.REGISTRATION_OPEN,
        "display_name": "报名开放",
        "description": "赛事接受报名中"
    },
    {
        "status_code": TournamentStatusCode.REGISTRATION_CLOSED,
        "display_name": "报名截止",
        "description": "报名已截止，准备开始比赛"
    },
    {
        "status_code": TournamentStatusCode.ONGOING,
        "display_name": "进行中",
        "description": "赛事正在进行中"
    },
    {
        "status_code": TournamentStatusCode.COMPLETED,
        "display_name": "已完成",
        "description": "赛事已结束"
    },
    {
        "status_code": TournamentStatusCode.CANCELLED,
        "display_name": "已取消",
        "description": "赛事已取消"
    }
]
