from django.db import models
from django.core.validators import MinLengthValidator
from uuid import uuid4

from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament
from backend.apps.fencing_organizer.modules.rule.models import DjangoRule
from backend.apps.fencing_organizer.modules.event_type.models import DjangoEventType
from backend.apps.fencing_organizer.modules.event_status.models import DjangoEventStatus


class DjangoEvent(models.Model):
    """比赛项目 Django ORM 模型"""

    # PK - UUID
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # 外键字段
    tournament = models.ForeignKey(
        DjangoTournament,
        on_delete=models.CASCADE,
        db_column='tournament_id',
        related_name='events',
        verbose_name="所属赛事"
    )

    rule = models.ForeignKey(
        DjangoRule,
        on_delete=models.PROTECT,
        db_column='rule_id',
        related_name='events',
        verbose_name="赛制规则"
    )

    event_type = models.ForeignKey(
        DjangoEventType,
        on_delete=models.PROTECT,
        db_column='event_type_id',
        related_name='events',
        verbose_name="项目类型"
    )

    status = models.ForeignKey(
        DjangoEventStatus,
        on_delete=models.PROTECT,
        db_column='status_id',
        related_name='events',
        verbose_name="项目状态"
    )

    # 必填字段
    event_name = models.CharField(
        max_length=200,
        verbose_name="项目名称",
        validators=[MinLengthValidator(1)]
    )

    is_team_event = models.BooleanField(
        default=False,
        verbose_name="是否为团体赛"
    )

    # 可选字段
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="项目开始时间"
    )

    # 时间戳字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'event'
        verbose_name = "比赛项目"
        verbose_name_plural = "比赛项目"
        ordering = ['start_time', 'event_name']
        indexes = [
            models.Index(fields=['tournament'], name='idx_event_tournament'),
            models.Index(fields=['status'], name='idx_event_status'),
            models.Index(fields=['event_type'], name='idx_event_type'),
            models.Index(fields=['start_time'], name='idx_event_start_time'),
            models.Index(fields=['is_team_event'], name='idx_event_is_team'),
        ]

    def __str__(self):
        return f"{self.event_name} ({self.tournament.tournament_name})"

    def save(self, *args, **kwargs):
        """保存前自动设置是否为团体赛"""
        if self.event_type:
            self.is_team_event = self.event_type.is_team
        super().save(*args, **kwargs)

    @property
    def weapon_type(self) -> str:
        """获取剑种"""
        return self.event_type.weapon_type if self.event_type else None

    @property
    def gender(self) -> str:
        """获取性别"""
        return self.event_type.gender if self.event_type else None

    @property
    def is_individual(self) -> bool:
        """是否为个人赛"""
        return not self.is_team_event

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status.status_code == "COMPLETED" if self.status else False

    @property
    def is_active(self) -> bool:
        """是否活跃（未完成）"""
        return not self.is_completed if self.status else False

    @property
    def participant_count(self) -> int:
        """参与者数量"""
        return 10
        # if self.is_team_event:
        #     from ..team.models import DjangoTeam
        #     return DjangoTeam.objects.filter(event=self).count()
        # else:
        #     from ..event_seed.models import DjangoEventSeed
        #     return DjangoEventSeed.objects.filter(event=self).count()

    @property
    def qualified_count(self) -> int:
        """晋级人数（根据规则）"""
        if self.is_team_event:
            # 团体赛晋级人数通常是固定数量或根据参赛队伍数量
            return min(self.participant_count, self.rule.total_qualified_count)
        else:
            # 个人赛使用规则中的总晋级人数
            return self.rule.total_qualified_count
