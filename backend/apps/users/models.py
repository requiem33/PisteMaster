from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        SCHEDULER = "SCHEDULER", "Scheduler"
        GUEST = "GUEST", "Guest"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SCHEDULER, verbose_name="role")

    class Meta:
        db_table = "users"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_scheduler(self):
        return self.role == self.Role.SCHEDULER

    @property
    def is_guest(self):
        return self.role == self.Role.GUEST
