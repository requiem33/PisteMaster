from django.db import models
from uuid import uuid4

from backend.apps.fencing_organizer.modules.elimination_type.models import DjangoEliminationType
from backend.apps.fencing_organizer.modules.ranking_type.models import DjangoRankingType


class DjangoRule(models.Model):
    """赛制规则 Django ORM 模型"""

    # PK - UUID
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # 必填字段
    rule_name = models.CharField(max_length=100, verbose_name="规则名称")
    total_qualified_count = models.IntegerField(verbose_name="总晋级人数")

    # 外键字段
    elimination_type = models.ForeignKey(
        DjangoEliminationType,
        on_delete=models.PROTECT,
        db_column='elimination_type_id',
        related_name='rules',
        verbose_name="淘汰赛类型"
    )

    final_ranking_type = models.ForeignKey(
        DjangoRankingType,
        on_delete=models.PROTECT,
        db_column='final_ranking_type_id',
        related_name='rules',
        verbose_name="名次决出方式"
    )

    # 可选字段
    match_format = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="单场比赛格式"
    )

    pool_size = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="小组赛每组人数"
    )

    match_duration = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="单局时长（秒）"
    )

    match_score_pool = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="小组赛目标分数"
    )

    match_score_elimination = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="淘汰赛目标分数"
    )

    group_qualification_ratio = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="晋级比例"
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="规则描述"
    )

    # 时间戳字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rule'
        verbose_name = "赛制规则"
        verbose_name_plural = "赛制规则"
        ordering = ['rule_name']
        indexes = [
            models.Index(fields=['elimination_type'], name='idx_rule_elimination_type'),
            models.Index(fields=['final_ranking_type'], name='idx_rule_ranking_type'),
            models.Index(fields=['pool_size'], name='idx_rule_pool_size'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(pool_size__gte=3) | models.Q(pool_size__isnull=True),
                name='chk_rule_pool_size'
            ),
            models.CheckConstraint(
                check=models.Q(group_qualification_ratio__gte=0)
                      & models.Q(group_qualification_ratio__lte=1)
                      | models.Q(group_qualification_ratio__isnull=True),
                name='chk_rule_qualification_ratio'
            ),
        ]

    def __str__(self):
        return f"{self.rule_name} ({self.elimination_type.display_name})"

    @property
    def is_single_elimination(self) -> bool:
        """是否为单败淘汰"""
        return self.elimination_type.type_code == "SINGLE_ELIMINATION"

    @property
    def is_double_elimination(self) -> bool:
        """是否为双败淘汰"""
        return self.elimination_type.type_code == "DOUBLE_ELIMINATION"

    @property
    def is_round_robin_only(self) -> bool:
        """是否为仅循环赛"""
        return self.elimination_type.type_code == "ROUND_ROBIN_ONLY"

    @property
    def has_bronze_match(self) -> bool:
        """是否有铜牌赛"""
        return self.final_ranking_type.type_code == "BRONZE_MATCH"
