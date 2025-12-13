from enum import StrEnum
from decimal import Decimal


class EliminationTypeCode(StrEnum):
    """淘汰赛类型代码枚举"""
    SINGLE_ELIMINATION = "SINGLE_ELIMINATION"  # 单败淘汰
    DOUBLE_ELIMINATION = "DOUBLE_ELIMINATION"  # 双败淘汰
    ROUND_ROBIN_ONLY = "ROUND_ROBIN_ONLY"  # 仅循环赛


class RankingTypeCode(StrEnum):
    """排名决出方式代码枚举"""
    BRONZE_MATCH = "BRONZE_MATCH"  # 有铜牌赛
    ALL_RANKS = "ALL_RANKS"  # 所有排名
    NO_THIRD_PLACE = "NO_THIRD_PLACE"  # 无铜牌赛


# 预定义淘汰赛类型
PREDEFINED_ELIMINATION_TYPES = [
    {
        "type_code": EliminationTypeCode.SINGLE_ELIMINATION,
        "display_name": "单败淘汰"
    },
    {
        "type_code": EliminationTypeCode.DOUBLE_ELIMINATION,
        "display_name": "双败淘汰"
    },
    {
        "type_code": EliminationTypeCode.ROUND_ROBIN_ONLY,
        "display_name": "仅循环赛"
    }
]

# 预定义排名类型
PREDEFINED_RANKING_TYPES = [
    {
        "type_code": RankingTypeCode.BRONZE_MATCH,
        "display_name": "有铜牌赛"
    },
    {
        "type_code": RankingTypeCode.ALL_RANKS,
        "display_name": "所有排名"
    },
    {
        "type_code": RankingTypeCode.NO_THIRD_PLACE,
        "display_name": "无铜牌赛"
    }
]

# 预定义规则
PREDEFINED_RULES = [
    {
        "rule_name": "FIE标准赛制",
        "elimination_type_code": EliminationTypeCode.SINGLE_ELIMINATION,
        "final_ranking_type_code": RankingTypeCode.BRONZE_MATCH,
        "match_format": "3x3分钟",
        "pool_size": 7,
        "match_duration": 180,  # 3分钟
        "match_score_pool": 5,
        "match_score_elimination": 15,
        "total_qualified_count": 24,
        "group_qualification_ratio": Decimal("0.5"),
        "description": "国际击剑联合会标准赛制：7人小组，5分制，淘汰赛15分制"
    },
    {
        "rule_name": "快速赛制",
        "elimination_type_code": EliminationTypeCode.SINGLE_ELIMINATION,
        "final_ranking_type_code": RankingTypeCode.NO_THIRD_PLACE,
        "match_format": "1x5分钟",
        "pool_size": 6,
        "match_duration": 300,  # 5分钟
        "match_score_pool": 10,
        "match_score_elimination": 15,
        "total_qualified_count": 16,
        "group_qualification_ratio": Decimal("0.6"),
        "description": "快速比赛赛制：6人小组，10分制"
    },
    {
        "rule_name": "青少年赛制",
        "elimination_type_code": EliminationTypeCode.SINGLE_ELIMINATION,
        "final_ranking_type_code": RankingTypeCode.ALL_RANKS,
        "match_format": "2x2分钟",
        "pool_size": 6,
        "match_duration": 120,  # 2分钟
        "match_score_pool": 5,
        "match_score_elimination": 10,
        "total_qualified_count": 16,
        "group_qualification_ratio": Decimal("0.5"),
        "description": "青少年比赛赛制：6人小组，5分制，淘汰赛10分制"
    },
    {
        "rule_name": "双败淘汰赛制",
        "elimination_type_code": EliminationTypeCode.DOUBLE_ELIMINATION,
        "final_ranking_type_code": RankingTypeCode.BRONZE_MATCH,
        "match_format": "3x3分钟",
        "pool_size": 7,
        "match_duration": 180,
        "match_score_pool": 5,
        "match_score_elimination": 15,
        "total_qualified_count": 24,
        "group_qualification_ratio": Decimal("0.5"),
        "description": "双败淘汰赛制，败者组有机会争夺冠军"
    },
    {
        "rule_name": "仅循环赛赛制",
        "elimination_type_code": EliminationTypeCode.ROUND_ROBIN_ONLY,
        "final_ranking_type_code": RankingTypeCode.ALL_RANKS,
        "match_format": "1x5分钟",
        "pool_size": 8,
        "match_duration": 300,
        "match_score_pool": 10,
        "match_score_elimination": None,
        "total_qualified_count": 8,  # 全部排名
        "group_qualification_ratio": Decimal("1.0"),
        "description": "仅进行循环赛，根据循环赛成绩直接排名"
    }
]
