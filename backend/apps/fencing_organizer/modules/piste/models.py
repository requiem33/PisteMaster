from django.db import models
from uuid import uuid4

from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament


class DjangoPiste(models.Model):
    """剑道 Django ORM 模型"""

    # PK - UUID
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # 外键字段
    tournament = models.ForeignKey(
        DjangoTournament,
        on_delete=models.CASCADE,
        db_column='tournament_id',
        related_name='pistes',
        verbose_name="所属赛事"
    )

    # 必填字段
    piste_number = models.CharField(
        max_length=10,
        verbose_name="剑道编号"
    )

    # 可选字段
    location = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="具体位置"
    )

    piste_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('MAIN', '主剑道'),
            ('SIDE', '副剑道'),
            ('WARMUP', '热身剑道'),
        ],
        verbose_name="剑道类型"
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name="是否可用"
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
        db_table = 'piste'
        verbose_name = "剑道"
        verbose_name_plural = "剑道"
        ordering = ['tournament', 'piste_number']
        constraints = [
            models.UniqueConstraint(
                fields=['tournament', 'piste_number'],
                name='unique_piste_tournament_number'
            )
        ]
        indexes = [
            models.Index(fields=['tournament', 'is_available'], name='idx_piste_availability'),
            models.Index(fields=['piste_type'], name='idx_piste_type'),
        ]

    def __str__(self):
        return f"剑道 {self.piste_number} ({self.tournament.tournament_name})"

    @property
    def is_main_piste(self) -> bool:
        """是否为主剑道"""
        return self.piste_type == 'MAIN'

    @property
    def is_warmup_piste(self) -> bool:
        """是否为热身剑道"""
        return self.piste_type == 'WARMUP'
