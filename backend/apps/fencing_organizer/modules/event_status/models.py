from django.db import models
from uuid import uuid4


class DjangoEventStatus(models.Model):
    """项目状态 Django ORM 模型"""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    status_code = models.CharField(max_length=20, unique=True, verbose_name="状态代码")
    display_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="显示名称")

    class Meta:
        db_table = 'event_status'
        verbose_name = "项目状态"
        verbose_name_plural = "项目状态"
        ordering = ['status_code']

    def __str__(self):
        return self.display_name or self.status_code
