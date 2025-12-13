from django.db import models
from uuid import uuid4


class DjangoRankingType(models.Model):
    """排名决出方式 Django ORM 模型"""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    type_code = models.CharField(max_length=30, unique=True, verbose_name="类型代码")
    display_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="显示名称")

    class Meta:
        db_table = 'ranking_type'
        verbose_name = "排名类型"
        verbose_name_plural = "排名类型"
        ordering = ['type_code']

    def __str__(self):
        return self.display_name or self.type_code
