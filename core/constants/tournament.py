from enum import StrEnum


class TournamentOrdering(StrEnum):
    """赛事排序选项"""
    START_DATE_ASC = "start_date"
    START_DATE_DESC = "-start_date"
    END_DATE_ASC = "end_date"
    END_DATE_DESC = "-end_date"
    CREATED_AT_ASC = "created_at"
    CREATED_AT_DESC = "-created_at"
    NAME_ASC = "tournament_name"
    NAME_DESC = "-tournament_name"
