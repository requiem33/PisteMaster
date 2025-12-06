# core/models/enums.py
from enum import Enum

class TournamentStatus(Enum):
    """赛事状态"""
    DRAFT = 'draft'                 # 草稿
    PUBLISHED = 'published'         # 已发布
    REGISTRATION_CLOSED = 'registration_closed'  # 报名截止
    ONGOING = 'ongoing'             # 进行中
    COMPLETED = 'completed'         # 已结束
    CANCELLED = 'cancelled'         # 已取消

class CompetitionStatus(Enum):
    DRAFT = 'draft'      # 草稿
    OPEN = 'open'        # 报名中
    CLOSED = 'closed'    # 报名截止
    ONGOING = 'ongoing'  # 进行中
    COMPLETED = 'completed' # 已结束
    CANCELLED = 'cancelled' # 已取消

class EventType(Enum):
    """比赛类型"""
    INDIVIDUAL = 'individual'      # 个人赛
    TEAM = 'team'                  # 团体赛

class WeaponType(Enum):
    """武器类型"""
    FOIL = 'foil'      # 花剑
    EPEE = 'epee'      # 重剑
    SABRE = 'sabre'    # 佩剑

class GenderCategory(Enum):
    """性别分组"""
    MEN = 'men'
    WOMEN = 'women'
    MIXED = 'mixed'    # 混合
    OPEN = 'open'      # 公开组

class AgeGroup(Enum):
    """年龄组别"""
    U14 = 'u14'
    U16 = 'u16'
    CADET = 'cadet'    # 青年组 (U18)
    JUNIOR = 'junior'  # 少年组 (U20)
    SENIOR = 'senior'  # 成年组
    VETERAN = 'veteran' # 老将组