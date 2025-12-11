from django.db import models
from uuid import uuid4


class DjangoFencer(models.Model):
    """用于与数据库交互的 Django ORM 模型"""

    # PK - UUID 对应 Dataclass 的 id
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # NOT NULL 字段
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # 可选字段 (null=True, blank=True)
    display_name = models.CharField(max_length=200, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    country_code = models.CharField(max_length=3, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    # UNIQUE 字段
    fencing_id = models.CharField(max_length=50, unique=True, null=True, blank=True)

    current_ranking = models.IntegerField(null=True, blank=True)
    primary_weapon = models.CharField(max_length=10, null=True, blank=True)

    # 时间戳字段 (auto_now_add/auto_now 用于保存时自动更新)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fencer'
        # 根据 Dataclass 建议添加索引
        indexes = [
            models.Index(fields=['country_code'], name='idx_fencer_country'),
            models.Index(fields=['last_name', 'first_name'], name='idx_fencer_name'),
            models.Index(fields=['fencing_id'], name='idx_fencer_fencing_id'),
        ]

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.country_code})"
