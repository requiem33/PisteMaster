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
    event = models.ForeignKey(
        DjangoEvent,
        on_delete=models.CASCADE,
        db_column='event_id',
        related_name='pools',
        verbose_name="所属项目"
    )

    piste = models.ForeignKey(
        DjangoPiste,
        on_delete=models.SET_NULL,
        db_column='piste_id',
        related_name='pools',
        null=True,
        blank=True,
        verbose_name="分配剑道"
    )

    # 必填字段
    pool_number = models.IntegerField(
        verbose_name="小组编号",
        validators=[MinValueValidator(1)]
    )

    # 可选字段
    pool_letter = models.CharField(
        max_length=1,
        null=True,
        blank=True,
        verbose_name="小组字母"
    )

    start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="开始时间"
    )

    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.value) for status in PoolStatus],
        default=PoolStatus.SCHEDULED.value,
        verbose_name="状态"
    )

    is_completed = models.BooleanField(
        default=False,
        verbose_name="是否完成"
    )

    # 时间戳字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pool'
        verbose_name = "小组"
        verbose_name_plural = "小组"
        ordering = ['event', 'pool_number']
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'pool_number'],
                name='unique_pool_event_number'
            )
        ]
        indexes = [
            models.Index(fields=['event'], name='idx_pool_event'),
            models.Index(fields=['piste'], name='idx_pool_piste'),
            models.Index(fields=['status'], name='idx_pool_status'),
            models.Index(fields=['is_completed'], name='idx_pool_completed'),
            models.Index(fields=['start_time'], name='idx_pool_start_time'),
        ]

    def __str__(self):
        letter = f" {self.pool_letter}" if self.pool_letter else ""
        return f"小组{self.pool_number}{letter} ({self.event.event_name})"

    def save(self, *args, **kwargs):
        """保存前自动处理状态与完成状态的一致性"""
        # 如果状态为已完成，自动设置is_completed为True
        if self.status == PoolStatus.COMPLETED.value:
            self.is_completed = True
        # 如果状态不为已完成但is_completed为True，重置状态
        elif self.status != PoolStatus.COMPLETED.value and self.is_completed:
            self.is_completed = False

        # 如果pool_letter为空，根据pool_number自动生成
        if not self.pool_letter and self.pool_number:
            self.pool_letter = self._number_to_letter(self.pool_number)

        super().save(*args, **kwargs)

    @staticmethod
    def _number_to_letter(number: int) -> str:
        """将数字转换为字母（1->A, 2->B, ..., 27->AA, 28->AB）"""
        result = ""
        while number > 0:
            number -= 1
            result = chr(number % 26 + ord('A')) + result
            number //= 26
        return result if result else "A"

    @property
    def display_name(self) -> str:
        """显示名称"""
        if self.pool_letter:
            return f"小组 {self.pool_letter}"
        return f"小组 {self.pool_number}"

    @property
    def is_active(self) -> bool:
        """是否活跃（非已完成/已取消）"""
        return self.status not in [PoolStatus.COMPLETED.value, PoolStatus.CANCELLED.value]

    @property
    def participant_count(self) -> int:
        """小组成员数量"""
        return self.participants.count()

    @property
    def bout_count(self) -> int:
        """小组比赛数量"""
        return self.bouts.count()

    @property
    def completed_bout_count(self) -> int:
        """已完成的比赛数量"""
        return self.bouts.filter(status__status_code='COMPLETED').count()

    @property
    def completion_percentage(self) -> float:
        """完成百分比"""
        if self.bout_count == 0:
            return 0.0
        return (self.completed_bout_count / self.bout_count) * 100
