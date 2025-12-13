from django.db import models
from uuid import uuid4


class DjangoEliminationType(models.Model):
    """淘汰赛类型 Django ORM 模型"""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    type_code = models.CharField(max_length=30, unique=True, verbose_name="类型代码")
    display_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="显示名称")

    class Meta:
        db_table = 'elimination_type'
        verbose_name = "淘汰赛类型"
        verbose_name_plural = "淘汰赛类型"
        ordering = ['type_code']

    def __str__(self):
        return self.display_name or self.type_code
