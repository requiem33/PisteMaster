from django.db import models
from uuid import uuid4


class DjangoEventType(models.Model):
    """项目类型 Django ORM 模型"""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    type_code = models.CharField(max_length=30, unique=True, verbose_name="类型代码")
    display_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="显示名称")
    weapon_type = models.CharField(max_length=10, null=True, blank=True, verbose_name="剑种")
    gender = models.CharField(max_length=10, null=True, blank=True, verbose_name="性别")

    class Meta:
        db_table = 'event_type'
        verbose_name = "项目类型"
        verbose_name_plural = "项目类型"
        ordering = ['type_code']
        indexes = [
            models.Index(fields=['weapon_type'], name='idx_event_type_weapon'),
            models.Index(fields=['gender'], name='idx_event_type_gender'),
        ]

    def __str__(self):
        return self.display_name or self.type_code

    @property
    def is_individual(self) -> bool:
        """是否为个人赛"""
        return 'TEAM' not in self.type_code

    @property
    def is_team(self) -> bool:
        """是否为团体赛"""
        return 'TEAM' in self.type_code
