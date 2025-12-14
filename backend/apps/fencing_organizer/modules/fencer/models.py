from typing import Optional

from django.db import models
from uuid import uuid4
from django.core.validators import MinLengthValidator


class DjangoFencer(models.Model):
    """击剑运动员 Django ORM 模型"""

    # PK - UUID
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # 基本字段
    first_name = models.CharField(
        max_length=100,
        verbose_name="名",
        validators=[MinLengthValidator(1)]
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name="姓",
        validators=[MinLengthValidator(1)]
    )
    display_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="显示名称"
    )

    # 个人信息
    gender = models.CharField(
        max_length=10,
        choices=[
            ('MEN', '男'),
            ('WOMEN', '女'),
            ('MIXED', '混合'),
            ('OPEN', '公开'),
        ],
        blank=True,
        null=True,
        verbose_name="性别"
    )

    country_code = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        verbose_name="国家代码",
        help_text="IOC 3字母代码"
    )

    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="出生日期"
    )

    # 击剑相关
    fencing_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="国际击剑ID"
    )

    current_ranking = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="当前世界排名"
    )

    primary_weapon = models.CharField(
        max_length=10,
        choices=[
            ('FOIL', '花剑'),
            ('EPEE', '重剑'),
            ('SABRE', '佩剑'),
        ],
        blank=True,
        null=True,
        verbose_name="主剑种"
    )

    # 时间戳字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fencer'
        verbose_name = "击剑运动员"
        verbose_name_plural = "击剑运动员"
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['country_code'], name='idx_fencer_country'),
            models.Index(fields=['last_name', 'first_name'], name='idx_fencer_name'),
            models.Index(fields=['fencing_id'], name='idx_fencer_fencing_id'),
            models.Index(fields=['current_ranking'], name='idx_fencer_ranking'),
            models.Index(fields=['primary_weapon'], name='idx_fencer_weapon'),
            models.Index(fields=['gender'], name='idx_fencer_gender'),
            models.Index(fields=['birth_date'], name='idx_fencer_birth_date'),
            models.Index(fields=['created_at'], name='idx_fencer_created_at'),
        ]

    def __str__(self):
        return self.display_name or f"{self.last_name} {self.first_name}"

    def save(self, *args, **kwargs):
        """保存时自动生成display_name"""
        if not self.display_name:
            self.display_name = f"{self.last_name} {self.first_name}"

        # 清理字段
        if self.country_code:
            self.country_code = self.country_code.upper().strip()

        if self.fencing_id:
            self.fencing_id = self.fencing_id.strip()

        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        """返回完整姓名"""
        return f"{self.last_name} {self.first_name}"

    @property
    def age(self) -> Optional[int]:
        """计算年龄"""
        if not self.birth_date:
            return None

        from datetime import date
        today = date.today()
        age = today.year - self.birth_date.year

        # 如果生日还没到，减一岁
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1

        return age

    @property
    def is_international(self) -> bool:
        """是否为国际击剑运动员（有国际ID）"""
        return bool(self.fencing_id)
