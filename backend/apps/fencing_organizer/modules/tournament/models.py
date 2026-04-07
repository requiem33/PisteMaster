from django.db import models
from django.core.validators import MinLengthValidator
from django.conf import settings
from uuid import uuid4


class DjangoTournament(models.Model):
    """赛事 Django ORM 模型"""

    class Status(models.TextChoices):
        PLANNING = "PLANNING", "计划中"
        REGISTRATION_OPEN = "REGISTRATION_OPEN", "报名开放"
        REGISTRATION_CLOSED = "REGISTRATION_CLOSED", "报名关闭"
        ONGOING = "ONGOING", "进行中"
        COMPLETED = "COMPLETED", "已完成"
        CANCELLED = "CANCELLED", "已取消"

    # PK - UUID
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # 必填字段
    tournament_name = models.CharField(max_length=200, verbose_name="赛事名称", validators=[MinLengthValidator(1)])

    start_date = models.DateField(verbose_name="开始日期")
    end_date = models.DateField(verbose_name="结束日期")

    # 外键字段
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PLANNING, verbose_name="赛事状态"  # 👈 默认状态为"计划中"
    )

    # 可选字段
    organizer = models.CharField(max_length=200, null=True, blank=True, verbose_name="主办方")

    location = models.CharField(max_length=200, null=True, blank=True, verbose_name="赛事举办地")

    # 用户关联字段
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tournaments",
        verbose_name="创建者",
    )
    schedulers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="assigned_tournaments", blank=True, verbose_name="编排人员")

    # 版本追踪字段
    version = models.BigIntegerField(default=1)
    last_modified_node = models.CharField(max_length=100, blank=True, default="")
    last_modified_at = models.DateTimeField(auto_now=True)

    # 时间戳字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tournament"
        verbose_name = "赛事"
        verbose_name_plural = "赛事"
        ordering = ["-start_date", "tournament_name"]
        indexes = [
            models.Index(fields=["start_date", "end_date"], name="idx_tournament_dates"),
            models.Index(fields=["status"], name="idx_tournament_status"),
            models.Index(fields=["tournament_name"], name="idx_tournament_name"),
        ]
        constraints = [models.CheckConstraint(check=models.Q(end_date__gte=models.F("start_date")), name="chk_tournament_dates_valid")]

    def __str__(self):
        return f"{self.tournament_name} ({self.start_date} - {self.end_date})"

    @property
    def duration_days(self) -> int:
        """计算赛事持续天数"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    @property
    def is_active(self) -> bool:
        """判断赛事是否活跃（计划中或进行中）"""
        active_statuses = ["PLANNING", "REGISTRATION_OPEN", "REGISTRATION_CLOSED", "ONGOING"]
        return self.status.status_code in active_statuses if self.status else False
