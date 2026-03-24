from django.db import models
from django.core.validators import MinValueValidator
from uuid import uuid4

from backend.apps.fencing_organizer.modules.event.models import DjangoEvent
from backend.apps.fencing_organizer.modules.piste.models import DjangoPiste
from core.constants.pool import PoolStatus


class DjangoPool(models.Model):
    """小组 Django ORM 模型"""

    # PK - UUID
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # 外键字段
    event = models.ForeignKey(DjangoEvent, on_delete=models.CASCADE, db_column="event_id", related_name="pools", verbose_name="所属项目")

    piste = models.ForeignKey(
        DjangoPiste, on_delete=models.SET_NULL, null=True, blank=True, db_column="piste_id", related_name="pools", verbose_name="分配剑道"
    )

    stage_id = models.CharField(max_length=50, default="1", verbose_name="阶段ID")

    # 必填字段
    pool_number = models.IntegerField(verbose_name="小组编号", validators=[MinValueValidator(1)])

    start_time = models.DateTimeField(null=True, blank=True, verbose_name="计划开始时间")

    # MVP 新增 JSON 字段
    fencer_ids = models.JSONField(default=list, blank=True, verbose_name="组内运动员ID列表(JSON)")

    results = models.JSONField(default=list, blank=True, verbose_name="比赛结果矩阵(JSON)")

    stats = models.JSONField(default=list, blank=True, verbose_name="比赛统计(JSON)")

    is_locked = models.BooleanField(default=False, verbose_name="是否锁定成绩")

    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.value) for status in PoolStatus],
        default=PoolStatus.SCHEDULED.value,
        verbose_name="状态",
    )

    is_completed = models.BooleanField(default=False, verbose_name="是否完成")

    # 时间戳字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pool"
        verbose_name = "小组"
        verbose_name_plural = "小组"
        ordering = ["event", "stage_id", "pool_number"]
        constraints = [models.UniqueConstraint(fields=["event", "stage_id", "pool_number"], name="unique_pool_event_stage_number")]
        indexes = [
            models.Index(fields=["event"], name="idx_pool_event"),
            models.Index(fields=["stage_id"], name="idx_pool_stage"),
            models.Index(fields=["status"], name="idx_pool_status"),
        ]

    def __str__(self):
        return f"阶段{self.stage_id} - 小组{self.pool_number} ({self.event.event_name})"

    def save(self, *args, **kwargs):
        """保存前自动处理状态与完成状态的一致性"""
        if self.status == PoolStatus.COMPLETED.value:
            self.is_completed = True
        elif self.status != PoolStatus.COMPLETED.value and self.is_completed:
            self.is_completed = False

        super().save(*args, **kwargs)
