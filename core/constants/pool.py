from enum import StrEnum


class PoolStatus(StrEnum):
    """小组状态枚举"""
    SCHEDULED = "SCHEDULED"  # 已安排
    READY = "READY"  # 准备就绪
    IN_PROGRESS = "IN_PROGRESS"  # 进行中
    COMPLETED = "COMPLETED"  # 已完成
    CANCELLED = "CANCELLED"  # 已取消
    POSTPONED = "POSTPONED"  # 已延期


class PoolLetter(StrEnum):
    """小组字母枚举"""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"
    J = "J"
    K = "K"
    L = "L"
    M = "M"
    N = "N"
    O = "O"
    P = "P"
    Q = "Q"
    R = "R"
    S = "S"
    T = "T"
    U = "U"
    V = "V"
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"


# 小组状态流转规则
STATUS_TRANSITIONS = {
    PoolStatus.SCHEDULED: [PoolStatus.READY, PoolStatus.CANCELLED, PoolStatus.POSTPONED],
    PoolStatus.READY: [PoolStatus.IN_PROGRESS, PoolStatus.SCHEDULED, PoolStatus.CANCELLED],
    PoolStatus.IN_PROGRESS: [PoolStatus.COMPLETED, PoolStatus.CANCELLED],
    PoolStatus.COMPLETED: [],
    PoolStatus.CANCELLED: [PoolStatus.SCHEDULED],
    PoolStatus.POSTPONED: [PoolStatus.SCHEDULED, PoolStatus.CANCELLED],
}
