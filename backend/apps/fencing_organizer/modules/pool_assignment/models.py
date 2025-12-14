from django.db import models
from django.core.validators import MinValueValidator
from uuid import uuid4

from backend.apps.fencing_organizer.modules.pool.models import DjangoPool
from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer


class DjangoPoolAssignment(models.Model):
    """Pool-Fencer关联 Django ORM 模型"""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    pool = models.ForeignKey(
        DjangoPool,
        on_delete=models.CASCADE,
        db_column='pool_id',
        related_name='assignments',
        verbose_name="所属小组"
    )

    fencer = models.ForeignKey(
        DjangoFencer,
        on_delete=models.CASCADE,
        db_column='fencer_id',
        related_name='pool_assignments',
        verbose_name="运动员"
    )

    final_pool_rank = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name="最终排名"
    )

    victories = models.IntegerField(
        default=0,
        verbose_name="胜场数(V)"
    )

    indicator = models.IntegerField(
        default=0,
        verbose_name="得失分差(Ind)",
        help_text="TS - TR，不允许直接更新"
    )

    touches_scored = models.IntegerField(
        default=0,
        verbose_name="总得分(TS)"
    )

    touches_received = models.IntegerField(
        default=0,
        verbose_name="总失分(TR)"
    )

    matches_played = models.IntegerField(
        default=0,
        verbose_name="已赛场次"
    )

    is_qualified = models.BooleanField(
        default=False,
        verbose_name="是否晋级"
    )

    qualification_rank = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="晋级排名"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pool_assignment'
        verbose_name = "小组分配"
        verbose_name_plural = "小组分配"
        ordering = ['pool', 'final_pool_rank']
        constraints = [
            models.UniqueConstraint(
                fields=['pool', 'fencer'],
                name='unique_pool_fencer'
            ),
            models.UniqueConstraint(
                fields=['pool', 'final_pool_rank'],
                condition=models.Q(final_pool_rank__isnull=False),
                name='unique_pool_rank'
            )
        ]
        indexes = [
            models.Index(fields=['pool', 'is_qualified', 'final_pool_rank'], name='idx_pool_assignment_qualified'),
            models.Index(fields=['fencer'], name='idx_pool_assignment_fencer'),
            models.Index(fields=['final_pool_rank'], name='idx_pool_assignment_rank'),
        ]

    def __str__(self):
        rank_str = f"#{self.final_pool_rank}" if self.final_pool_rank else "未排名"
        return f"{self.fencer.display_name} - {self.pool.display_name} ({rank_str})"

    def save(self, *args, **kwargs):
        """保存前自动计算indicator"""
        # 自动计算得失分差（根据击剑规则）
        self.indicator = self.touches_scored - self.touches_received

        # 确保数据一致性
        if self.matches_played < 0:
            self.matches_played = 0
        if self.victories < 0:
            self.victories = 0
        if self.victories > self.matches_played:
            self.victories = self.matches_played

        super().save(*args, **kwargs)

    @property
    def win_rate(self) -> float:
        """胜率"""
        if self.matches_played == 0:
            return 0.0
        return (self.victories / self.matches_played) * 100

    @property
    def average_touches_scored(self) -> float:
        """平均每场得分"""
        if self.matches_played == 0:
            return 0.0
        return self.touches_scored / self.matches_played

    @property
    def average_touches_received(self) -> float:
        """平均每场失分"""
        if self.matches_played == 0:
            return 0.0
        return self.touches_received / self.matches_played
