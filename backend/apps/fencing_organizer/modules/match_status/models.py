from django.db import models
from uuid import uuid4


class DjangoMatchStatusType(models.Model):
    """比赛状态类型 Django ORM 模型"""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    status_code = models.CharField(max_length=20, unique=True, verbose_name="状态代码")
    description = models.CharField(max_length=100, null=True, blank=True, verbose_name="描述")

    class Meta:
        db_table = 'match_status_type'
        verbose_name = "比赛状态"
        verbose_name_plural = "比赛状态"
        ordering = ['status_code']

    def __str__(self):
        return f"{self.status_code} ({self.description or '无描述'})"
