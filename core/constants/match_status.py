from enum import StrEnum


class MatchStatusCode(StrEnum):
    """比赛状态代码枚举"""
    SCHEDULED = "SCHEDULED"  # 已安排
    READY = "READY"  # 准备就绪
    IN_PROGRESS = "IN_PROGRESS"  # 进行中
    COMPLETED = "COMPLETED"  # 已完成
    FORFEITED = "FORFEITED"  # 弃权
    CANCELLED = "CANCELLED"  # 已取消
    POSTPONED = "POSTPONED"  # 已延期


# 预定义比赛状态
PREDEFINED_MATCH_STATUSES = [
    {
        "status_code": MatchStatusCode.SCHEDULED,
        "description": "比赛已安排"
    },
    {
        "status_code": MatchStatusCode.READY,
        "description": "比赛准备就绪"
    },
    {
        "status_code": MatchStatusCode.IN_PROGRESS,
        "description": "比赛进行中"
    },
    {
        "status_code": MatchStatusCode.COMPLETED,
        "description": "比赛已完成"
    },
    {
        "status_code": MatchStatusCode.FORFEITED,
        "description": "比赛弃权"
    },
    {
        "status_code": MatchStatusCode.CANCELLED,
        "description": "比赛已取消"
    },
    {
        "status_code": MatchStatusCode.POSTPONED,
        "description": "比赛已延期"
    }
]
