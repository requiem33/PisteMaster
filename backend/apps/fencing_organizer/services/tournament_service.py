from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, timedelta
from django.db import IntegrityError, transaction

from core.models.tournament import Tournament
from backend.apps.fencing_organizer.repositories.tournament_repo import DjangoTournamentRepository


class TournamentService:
    """赛事业务服务"""

    def __init__(self, repository: Optional[DjangoTournamentRepository] = None):
        self.repository = repository or DjangoTournamentRepository()

    def get_tournament_by_id(self, tournament_id: UUID) -> Optional[Tournament]:
        """根据ID获取赛事"""
        return self.repository.get_tournament_by_id(tournament_id)

    def get_all_tournaments(self) -> List[Tournament]:
        """获取所有赛事"""
        return self.repository.get_all_tournaments()

    def get_upcoming_tournaments(self, days: int = 30) -> List[Tournament]:
        """获取即将到来的赛事（未来N天内）"""
        today = date.today()
        future_date = today + timedelta(days=days)

        tournaments = self.repository.get_tournaments_by_date_range(today, future_date)
        # 过滤出未结束的赛事
        return [t for t in tournaments if t.end_date >= today]

    def get_ongoing_tournaments(self) -> List[Tournament]:
        """获取进行中的赛事"""
        today = date.today()
        tournaments = self.repository.get_tournaments_by_date_range(today, today)

        # 进一步过滤状态为ONGOING的赛事
        return [t for t in tournaments if t.status == "ONGOING"]

    def create_tournament(self, tournament_data: dict) -> Tournament:
        """
        创建赛事
        :param tournament_data: 经过 Serializer 验证的、干净的数据字典
        """
        try:
            # 2. 创建领域实体
            tournament_entity = Tournament(
                tournament_name=tournament_data['tournament_name'],
                start_date=tournament_data['start_date'],
                end_date=tournament_data['end_date'],
                organizer=tournament_data.get('organizer'),
                location=tournament_data.get('location'),
                status=tournament_data.get('status', 'PLANNING')
            )

            # 3. 通过 Repository 保存
            return self.repository.save_tournament(tournament_entity)

        except IntegrityError as e:
            raise self.TournamentServiceError(f"数据库完整性错误: {str(e)}")
        except KeyError as e:
            raise self.TournamentServiceError(f"缺少必要字段: {str(e)}")
        except Exception as e:
            raise self.TournamentServiceError(f"创建赛事时发生未知错误: {str(e)}")

    def update_tournament(self, tournament_id: UUID, tournament_data: dict) -> Tournament:
        """更新赛事"""
        # 检查赛事是否存在
        existing_tournament = self.repository.get_tournament_by_id(tournament_id)
        if not existing_tournament:
            raise self.TournamentServiceError(f"赛事 {tournament_id} 不存在")

        # 验证数据
        self._validate_tournament_data(tournament_data, is_create=False)

        # 更新属性
        for key, value in tournament_data.items():
            if hasattr(existing_tournament, key):
                setattr(existing_tournament, key, value)

        # 通过Repository保存
        try:
            return self.repository.save_tournament(existing_tournament)
        except IntegrityError as e:
            raise self.TournamentServiceError(f"更新赛事失败: {str(e)}")

    def delete_tournament(self, tournament_id: UUID) -> bool:
        """删除赛事"""
        # 检查赛事是否存在
        tournament = self.repository.get_tournament_by_id(tournament_id)
        if not tournament:
            return False

        # 删除赛事
        return self.repository.delete_tournament(tournament_id)

    def search_tournaments(self, **filters) -> List[Tournament]:
        """搜索赛事"""
        return self.repository.search_tournaments(**filters)

    def _validate_tournament_data(self, data: dict, is_create: bool = True) -> None:
        """验证赛事数据"""
        errors = {}

        # 必填字段检查
        if is_create:
            required_fields = ['tournament_name', 'start_date', 'end_date']
            for field in required_fields:
                if not data.get(field):
                    errors[field] = f"{field} 不能为空"

        # 日期验证
        if data.get('start_date') and data.get('end_date'):
            if data['end_date'] < data['start_date']:
                errors['end_date'] = "结束日期不能早于开始日期"

        # 字段长度验证
        if data.get('tournament_name') and len(data['tournament_name']) > 200:
            errors['tournament_name'] = "赛事名称长度不能超过200个字符"

        if data.get('organizer') and len(data['organizer']) > 200:
            errors['organizer'] = "主办方长度不能超过200个字符"

        if data.get('location') and len(data['location']) > 200:
            errors['location'] = "赛事举办地长度不能超过200个字符"

        if errors:
            raise self.TournamentServiceError("数据验证失败", errors)

    class TournamentServiceError(Exception):
        """Service层异常"""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
