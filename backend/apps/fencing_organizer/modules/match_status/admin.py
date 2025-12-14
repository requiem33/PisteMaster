from django.contrib import admin
from .models import DjangoMatchStatusType


@admin.register(DjangoMatchStatusType)
class MatchStatusTypeAdmin(admin.ModelAdmin):
    """淘汰赛类型管理后台"""

    list_display = ('status_code', 'description')
    search_fields = ('status_code', 'description')
    ordering = ('status_code',)
