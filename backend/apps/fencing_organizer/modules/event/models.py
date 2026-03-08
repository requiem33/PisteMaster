from django.db import models
from django.core.validators import MinLengthValidator
from uuid import uuid4

from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament
from backend.apps.fencing_organizer.modules.rule.models import DjangoRule


class DjangoEvent(models.Model):
    """比赛项目 Django ORM 模型"""

    class Status(models.TextChoices):
        REGISTRATION = 'REGISTRATION', '正在报名'
        ONGOING = 'ONGOING', '进行中'
        COMPLETED = 'COMPLETED', '已完成'
        CANCELLED = 'CANCELLED', '已取消'

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
        verbose_name="赛制规则",
        null=True,
        blank=True
    )

    event_type = models.CharField(
        max_length=50,
        verbose_name="项目类型(如MEN_INDIVIDUAL_FOIL)",
        default="",
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REGISTRATION,
        verbose_name="项目状态"
    )

    current_step = models.IntegerField(
        default=0,
        verbose_name="当前编排步骤进度"
    )

    live_ranking = models.JSONField(
        default=list,
        blank=True,
        verbose_name="实时排名快照(JSON)"
    )

    de_trees = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="各阶段淘汰赛对阵图(JSON)"
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
            models.Index(fields=['start_time'], name='idx_event_start_time'),
        ]

    def __str__(self):
        return f"{self.event_name} ({self.tournament.tournament_name})"

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == "COMPLETED"

    @property
    def is_active(self) -> bool:
        """是否活跃（未完成）"""
        return not self.is_completed

    @property
    def participant_count(self) -> int:
        """参与者数量"""
        return 10
        # 如果需要实际统计，可查询关联表

    @property
    def qualified_count(self) -> int:
        """晋级人数（根据规则）"""
        if self.rule:
            return self.rule.total_qualified_count
        return 0
