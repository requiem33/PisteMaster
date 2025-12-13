from enum import StrEnum


class EventStatusCode(StrEnum):
    """项目状态代码枚举"""
    SCHEDULED = "SCHEDULED"  # 已安排
    POOL_ROUND = "POOL_ROUND"  # 小组赛阶段
    ELIMINATION_ROUND = "ELIMINATION_ROUND"  # 淘汰赛阶段
    COMPLETED = "COMPLETED"  # 已完成
    CANCELLED = "CANCELLED"  # 已取消


class EventTypeCode(StrEnum):
    """项目类型代码枚举"""
    # 个人赛
    MEN_INDIVIDUAL_FOIL = "MEN_INDIVIDUAL_FOIL"
    MEN_INDIVIDUAL_EPEE = "MEN_INDIVIDUAL_EPEE"
    MEN_INDIVIDUAL_SABRE = "MEN_INDIVIDUAL_SABRE"
    WOMEN_INDIVIDUAL_FOIL = "WOMEN_INDIVIDUAL_FOIL"
    WOMEN_INDIVIDUAL_EPEE = "WOMEN_INDIVIDUAL_EPEE"
    WOMEN_INDIVIDUAL_SABRE = "WOMEN_INDIVIDUAL_SABRE"

    # 团体赛
    MEN_TEAM_FOIL = "MEN_TEAM_FOIL"
    MEN_TEAM_EPEE = "MEN_TEAM_EPEE"
    MEN_TEAM_SABRE = "MEN_TEAM_SABRE"
    WOMEN_TEAM_FOIL = "WOMEN_TEAM_FOIL"
    WOMEN_TEAM_EPEE = "WOMEN_TEAM_EPEE"
    WOMEN_TEAM_SABRE = "WOMEN_TEAM_SABRE"


class WeaponType(StrEnum):
    """剑种类型"""
    FOIL = "FOIL"  # 花剑
    EPEE = "EPEE"  # 重剑
    SABRE = "SABRE"  # 佩剑


class GenderType(StrEnum):
    """性别类型"""
    MEN = "MEN"
    WOMEN = "WOMEN"
    MIXED = "MIXED"
    OPEN = "OPEN"


# 预定义项目状态
PREDEFINED_EVENT_STATUSES = [
    {
        "status_code": EventStatusCode.SCHEDULED,
        "display_name": "已安排"
    },
    {
        "status_code": EventStatusCode.POOL_ROUND,
        "display_name": "小组赛阶段"
    },
    {
        "status_code": EventStatusCode.ELIMINATION_ROUND,
        "display_name": "淘汰赛阶段"
    },
    {
        "status_code": EventStatusCode.COMPLETED,
        "display_name": "已完成"
    },
    {
        "status_code": EventStatusCode.CANCELLED,
        "display_name": "已取消"
    }
]

# 预定义项目类型
PREDEFINED_EVENT_TYPES = [
    # 男子个人
    {
        "type_code": EventTypeCode.MEN_INDIVIDUAL_FOIL,
        "display_name": "男子个人花剑",
        "weapon_type": WeaponType.FOIL,
        "gender": GenderType.MEN
    },
    {
        "type_code": EventTypeCode.MEN_INDIVIDUAL_EPEE,
        "display_name": "男子个人重剑",
        "weapon_type": WeaponType.EPEE,
        "gender": GenderType.MEN
    },
    {
        "type_code": EventTypeCode.MEN_INDIVIDUAL_SABRE,
        "display_name": "男子个人佩剑",
        "weapon_type": WeaponType.SABRE,
        "gender": GenderType.MEN
    },
    # 女子个人
    {
        "type_code": EventTypeCode.WOMEN_INDIVIDUAL_FOIL,
        "display_name": "女子个人花剑",
        "weapon_type": WeaponType.FOIL,
        "gender": GenderType.WOMEN
    },
    {
        "type_code": EventTypeCode.WOMEN_INDIVIDUAL_EPEE,
        "display_name": "女子个人重剑",
        "weapon_type": WeaponType.EPEE,
        "gender": GenderType.WOMEN
    },
    {
        "type_code": EventTypeCode.WOMEN_INDIVIDUAL_SABRE,
        "display_name": "女子个人佩剑",
        "weapon_type": WeaponType.SABRE,
        "gender": GenderType.WOMEN
    },
    # 男子团体
    {
        "type_code": EventTypeCode.MEN_TEAM_FOIL,
        "display_name": "男子团体花剑",
        "weapon_type": WeaponType.FOIL,
        "gender": GenderType.MEN,
        "is_team": True
    },
    {
        "type_code": EventTypeCode.MEN_TEAM_EPEE,
        "display_name": "男子团体重剑",
        "weapon_type": WeaponType.EPEE,
        "gender": GenderType.MEN,
        "is_team": True
    },
    {
        "type_code": EventTypeCode.MEN_TEAM_SABRE,
        "display_name": "男子团体佩剑",
        "weapon_type": WeaponType.SABRE,
        "gender": GenderType.MEN,
        "is_team": True
    },
    # 女子团体
    {
        "type_code": EventTypeCode.WOMEN_TEAM_FOIL,
        "display_name": "女子团体花剑",
        "weapon_type": WeaponType.FOIL,
        "gender": GenderType.WOMEN,
        "is_team": True
    },
    {
        "type_code": EventTypeCode.WOMEN_TEAM_EPEE,
        "display_name": "女子团体重剑",
        "weapon_type": WeaponType.EPEE,
        "gender": GenderType.WOMEN,
        "is_team": True
    },
    {
        "type_code": EventTypeCode.WOMEN_TEAM_SABRE,
        "display_name": "女子团体佩剑",
        "weapon_type": WeaponType.SABRE,
        "gender": GenderType.WOMEN,
        "is_team": True
    }
]
