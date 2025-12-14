from uuid import uuid4

from django.db import models

from backend.apps.fencing_organizer.modules.pool.models import DjangoPool
from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
from backend.apps.fencing_organizer.modules.match_status.models import DjangoMatchStatusType


class DjangoPoolBout(models.Model):
    """小组赛单场 Django ORM 模型"""

    # PK - UUID
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # 外键字段
    pool = models.ForeignKey(
        DjangoPool,
        on_delete=models.CASCADE,
        db_column='pool_id',
        related_name='bouts',
        verbose_name="所属小组"
    )

    fencer_a = models.ForeignKey(
        DjangoFencer,
        on_delete=models.CASCADE,
        db_column='fencer_a_id',
        related_name='pool_bouts_as_a',
        verbose_name="运动员A"
    )

    fencer_b = models.ForeignKey(
        DjangoFencer,
        on_delete=models.CASCADE,
        db_column='fencer_b_id',
        related_name='pool_bouts_as_b',
        verbose_name="运动员B"
    )

    winner = models.ForeignKey(
        DjangoFencer,
        on_delete=models.SET_NULL,
        db_column='winner_id',
        related_name='pool_bouts_won',
        null=True,
        blank=True,
        verbose_name="获胜者"
    )

    status = models.ForeignKey(
        DjangoMatchStatusType,
        on_delete=models.PROTECT,
        db_column='status_id',
        related_name='pool_bouts',
        verbose_name="比赛状态"
    )

    # 比赛数据
    fencer_a_score = models.IntegerField(
        default=0,
        verbose_name="A得分"
    )

    fencer_b_score = models.IntegerField(
        default=0,
        verbose_name="B得分"
    )

    scheduled_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="计划时间"
    )

    actual_start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="实际开始时间"
    )

    actual_end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="实际结束时间"
    )

    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="持续时间（秒）"
    )

    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name="备注"
    )

    # 时间戳字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pool_bout'
        verbose_name = "小组赛单场"
        verbose_name_plural = "小组赛单场"
        ordering = ['pool', 'scheduled_time']
        constraints = [
            models.CheckConstraint(
                check=models.Q(fencer_a_id__lt=models.F('fencer_b_id')),
                name='chk_pool_bout_fencer_order'
            ),
            models.UniqueConstraint(
                fields=['pool', 'fencer_a', 'fencer_b'],
                name='unique_pool_bout_pair'
            )
        ]
        indexes = [
            models.Index(fields=['pool'], name='idx_pool_bout_pool'),
            models.Index(fields=['status'], name='idx_pool_bout_status'),
            models.Index(fields=['fencer_a', 'fencer_b'], name='idx_pool_bout_fencers'),
            models.Index(fields=['scheduled_time'], name='idx_pool_bout_scheduled_time'),
        ]

    def save(self, *args, **kwargs):
        """保存前自动计算胜者和验证"""
        # 验证运动员不能相同
        if self.fencer_a_id == self.fencer_b_id:
            raise ValueError("运动员A和运动员B不能是同一人")

        # 确保fencer_a_id < fencer_b_id（以满足唯一性约束）
        if self.fencer_a_id > self.fencer_b_id:
            self.fencer_a_id, self.fencer_b_id = self.fencer_b_id, self.fencer_a_id
            self.fencer_a_score, self.fencer_b_score = self.fencer_b_score, self.fencer_a_score

        # 自动计算获胜者（如果比赛已完成且有比分）
        if self.status.status_code == 'COMPLETED' and self.winner_id is None:
            if self.fencer_a_score > self.fencer_b_score:
                self.winner_id = self.fencer_a_id
            elif self.fencer_b_score > self.fencer_a_score:
                self.winner_id = self.fencer_b_id
            # 平局时winner_id保持为空

        # 计算持续时间
        if self.actual_start_time and self.actual_end_time:
            delta = self.actual_end_time - self.actual_start_time
            self.duration_seconds = int(delta.total_seconds())

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fencer_a} vs {self.fencer_b} (小组{self.pool.pool_number})"

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status.status_code == 'COMPLETED'

    @property
    def is_draw(self) -> bool:
        """是否为平局"""
        return self.fencer_a_score == self.fencer_b_score and self.is_completed

    @property
    def is_forfeited(self) -> bool:
        """是否为弃权"""
        return self.status.status_code in ['FORFEITED', 'WITHDRAWAL', 'DISQUALIFICATION']

    @property
    def is_ready_to_start(self) -> bool:
        """是否准备开始"""
        return self.status.status_code in ['SCHEDULED', 'READY']

    @property
    def target_score(self) -> int:
        """目标分数（从小组的规则中获取）"""
        if hasattr(self.pool, 'event') and hasattr(self.pool.event, 'rule'):
            return self.pool.event.rule.match_score_pool or 5  # 默认为5分
        return 5

    @property
    def is_score_valid(self) -> bool:
        """比分是否有效"""
        if self.is_completed:
            # 完成的比赛：比分不能超过目标分数
            max_score = self.target_score
            return self.fencer_a_score <= max_score and self.fencer_b_score <= max_score
        return True

    @property
    def display_name(self) -> str:
        """显示名称"""
        return f"{self.fencer_a.display_name} vs {self.fencer_b.display_name}"
