from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from django.db import IntegrityError, transaction

from core.models.event import Event
from backend.apps.fencing_organizer.repositories.event_repo import DjangoEventRepository
from backend.apps.fencing_organizer.repositories.tournament_repo import DjangoTournamentRepository
from backend.apps.fencing_organizer.repositories.rule_repo import DjangoRuleRepository


class EventService:
    """比赛项目业务服务"""

    def __init__(self,
                 event_repository: Optional[DjangoEventRepository] = None,
                 tournament_repository: Optional[DjangoTournamentRepository] = None,
                 rule_repository: Optional[DjangoRuleRepository] = None):

        self.event_repository = event_repository or DjangoEventRepository()
        self.tournament_repository = tournament_repository or DjangoTournamentRepository()
        self.rule_repository = rule_repository or DjangoRuleRepository()

    def get_event_by_id(self, event_id: UUID) -> Optional[Event]:
        """根据ID获取项目"""
        return self.event_repository.get_event_by_id(event_id)

    def get_events_by_tournament(self, tournament_id: UUID) -> List[Event]:
        """根据赛事获取项目"""
        return self.event_repository.get_events_by_tournament(tournament_id)

    def get_upcoming_events(self, days: int = 7) -> List[Event]:
        """获取即将到来的项目（未来N天内）"""
        now = datetime.now()
        future_date = now + timedelta(days=days)

        events = self.event_repository.get_upcoming_events(now, future_date)
        # 过滤掉已完成和已取消的项目
        return [e for e in events if not self._is_completed_or_cancelled(e)]

    def get_active_events(self) -> List[Event]:
        """获取活跃的项目（未完成且未取消）"""
        all_events = self.event_repository.get_all_events()
        return [e for e in all_events if not self._is_completed_or_cancelled(e)]

    def create_event(self, event_data: dict) -> Event:
        """创建项目"""
        # 验证数据
        self._validate_event_data(event_data, is_create=True)

        # 验证外键存在性
        self._validate_foreign_keys(event_data)

        # 创建Domain对象
        event = Event(
            tournament_id=event_data['tournament_id'],
            event_name=event_data['event_name'],
            rule_id=event_data.get('rule_id'),
            event_type=event_data.get('event_type', ''),
            status=event_data.get('status', 'REGISTRATION'),
            is_team_event=event_data.get('is_team_event', False),
            start_time=event_data.get('start_time')
        )

        # 通过Repository保存
        try:
            return self.event_repository.save_event(event)
        except IntegrityError as e:
            raise self.EventServiceError(f"创建项目失败: {str(e)}")

    def update_event(self, event_id: UUID, event_data: dict) -> Event:
        """更新项目"""
        # 检查项目是否存在
        existing_event = self.event_repository.get_event_by_id(event_id)
        if not existing_event:
            raise self.EventServiceError(f"项目 {event_id} 不存在")

        # 验证数据
        self._validate_event_data(event_data, is_create=False)

        # 验证外键存在性（如果有的话）
        self._validate_foreign_keys(event_data)

        # 更新属性
        for key, value in event_data.items():
            if hasattr(existing_event, key):
                setattr(existing_event, key, value)

        # 通过Repository保存
        try:
            return self.event_repository.save_event(existing_event)
        except IntegrityError as e:
            raise self.EventServiceError(f"更新项目失败: {str(e)}")

    def delete_event(self, event_id: UUID) -> bool:
        """删除项目"""
        # 检查项目是否存在
        event = self.event_repository.get_event_by_id(event_id)
        if not event:
            return False

        # 删除项目
        return self.event_repository.delete_event(event_id)

    def search_events(self, **filters) -> List[Event]:
        """搜索项目"""
        return self.event_repository.search_events(**filters)

    def initialize_predefined_data(self) -> Dict[str, int]:
        """初始化预定义数据（项目状态、项目类型）已简化为不使用DB记录"""
        return {
            "event_statuses": 0,
            "event_types": 0
        }

    def _validate_event_data(self, data: dict, is_create: bool = True) -> None:
        """验证项目数据"""
        errors = {}

        # 必填字段检查
        if is_create:
            required_fields = ['tournament_id', 'event_name']
            for field in required_fields:
                if not data.get(field):
                    errors[field] = f"{field} 不能为空"

        # 字段长度验证
        if data.get('event_name') and len(data['event_name']) > 200:
            errors['event_name'] = "项目名称长度不能超过200个字符"

        # 布尔值验证
        if 'is_team_event' in data and not isinstance(data['is_team_event'], bool):
            errors['is_team_event'] = "是否为团体赛必须是布尔值"

        if errors:
            raise self.EventServiceError("数据验证失败", errors)

    def _validate_foreign_keys(self, data: dict) -> None:
        """验证外键存在性"""
        if 'tournament_id' in data:
            tournament = self.tournament_repository.get_tournament_by_id(data['tournament_id'])
            if not tournament:
                raise self.EventServiceError(f"赛事 {data['tournament_id']} 不存在")

        if data.get('rule_id'):
            rule = self.rule_repository.get_rule_by_id(data['rule_id'])
            if not rule:
                raise self.EventServiceError(f"规则 {data['rule_id']} 不存在")

    def _is_completed_or_cancelled(self, event: Event) -> bool:
        """检查项目是否已完成或已取消"""
        return event.status in ['COMPLETED', 'CANCELLED']

    class EventServiceError(Exception):
        """Service层异常"""

        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
