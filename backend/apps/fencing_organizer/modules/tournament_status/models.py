from django.db import models
from uuid import uuid4


class DjangoTournamentStatus(models.Model):
    """赛事状态 Django ORM 模型"""

    # PK - UUID
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # UNIQUE 字段
    status_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="状态代码"
    )

    # 可选字段
    display_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="显示名称"
    )

    description = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="描述"
    )

    # 时间戳字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tournament_status'
        verbose_name = "赛事状态"
        verbose_name_plural = "赛事状态"
        ordering = ['status_code']

    def __str__(self):
        return f"{self.display_name or self.status_code}"
