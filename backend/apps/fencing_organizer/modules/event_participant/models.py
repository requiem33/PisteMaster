from django.db import models
from uuid import uuid4

from backend.apps.fencing_organizer.modules.event.models import DjangoEvent
from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer


class DjangoEventParticipant(models.Model):
    """Event-Fencer关联 Django ORM 模型"""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    event = models.ForeignKey(
        DjangoEvent,
        on_delete=models.CASCADE,
        db_column='event_id',
        related_name='participants',
        verbose_name="所属项目"
    )

    fencer = models.ForeignKey(
        DjangoFencer,
        on_delete=models.CASCADE,
        db_column='fencer_id',
        related_name='event_participations',
        verbose_name="运动员"
    )

    seed_rank = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="种子排名"
    )

    seed_value = models.FloatField(
        null=True,
        blank=True,
        verbose_name="种子分值"
    )

    is_confirmed = models.BooleanField(
        default=True,
        verbose_name="是否确认参赛"
    )

    registration_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="报名时间"
    )

    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name="备注"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'event_participant'
        verbose_name = "项目参与者"
        verbose_name_plural = "项目参与者"
        ordering = ['event', 'seed_rank']
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'fencer'],
                name='unique_event_fencer'
            )
        ]
        indexes = [
            models.Index(fields=['event', 'seed_rank'], name='idx_event_participant_seed'),
            models.Index(fields=['fencer'], name='idx_event_participant_fencer'),
            models.Index(fields=['is_confirmed'], name='idx_event_participant_conf'),
        ]

    def __str__(self):
        return f"{self.fencer.display_name} - {self.event.event_name}"

    def save(self, *args, **kwargs):
        """保存前自动设置报名时间"""
        if not self.registration_time:
            from django.utils.timezone import now
            self.registration_time = now()
        super().save(*args, **kwargs)
