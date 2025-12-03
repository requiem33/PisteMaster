from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Fencer(models.Model):
    """Django 数据库模型，对应 core.models.Fencer 核心业务对象。"""
    # ========== 核心身份信息 ==========
    first_name = models.CharField(max_length=50, verbose_name='名')
    last_name = models.CharField(max_length=50, verbose_name='姓')
    country = models.CharField(max_length=3, default='CHN', verbose_name='国家/地区代码')
    region = models.CharField(max_length=100, blank=True, null=True, verbose_name='地区/省份')
    club = models.CharField(max_length=150, blank=True, null=True, verbose_name='俱乐部')

    # ========== 个人特征信息 ==========
    date_of_birth = models.DateField(blank=True, null=True, verbose_name='出生日期')

    # 性别选择，使用明确选项
    class Gender(models.TextChoices):
        MALE = 'M', '男'
        FEMALE = 'F', '女'
        OTHER = 'O', '其他'
        NOT_SPECIFIED = 'N', '未指定'

    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        default=Gender.NOT_SPECIFIED,
        verbose_name='性别'
    )

    # ========== 业务属性 ==========
    # 武器种类选择
    class WeaponType(models.TextChoices):
        FOIL = 'Foil', '花剑'
        EPEE = 'Epee', '重剑'
        SABRE = 'Sabre', '佩剑'
        UNSPECIFIED = '', '未指定'

    weapon = models.CharField(
        max_length=10,
        choices=WeaponType.choices,
        blank=True,
        default=WeaponType.UNSPECIFIED,
        verbose_name='主项武器'
    )

    rating = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='积分'
    )

    seed = models.PositiveIntegerField(blank=True, null=True, verbose_name='种子排位')

    # ========== 状态与元数据 ==========
    # 状态选择
    class Status(models.TextChoices):
        ACTIVE = 'active', '活跃'
        RETIRED = 'retired', '退役'
        SUSPENDED = 'suspended', '禁赛'
        INJURED = 'injured', '伤病'

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='状态'
    )

    # 系统字段
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    # 唯一关联引用 (可选，用于快速反向查找)
    core_object_hash = models.CharField(max_length=64, blank=True, editable=False)

    class Meta:
        verbose_name = '击剑运动员'
        verbose_name_plural = '击剑运动员'
        # 姓名+国家可能作为简易唯一约束，实际项目可能需要更严谨方案
        unique_together = [['first_name', 'last_name', 'country']]
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.last_name} {self.first_name} ({self.country})'

    @property
    def full_name(self):
        """获取全名，与 core.Fencer 保持一致。"""
        return f'{self.last_name} {self.first_name}'

    @property
    def age(self):
        """计算年龄，与 core.Fencer 逻辑一致。"""
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        age = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age