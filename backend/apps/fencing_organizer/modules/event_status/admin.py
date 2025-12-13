from django.contrib import admin
from .models import DjangoEventStatus


@admin.register(DjangoEventStatus)
class EventStatusAdmin(admin.ModelAdmin):
    """项目状态管理后台"""

    list_display = ('status_code', 'display_name')
    search_fields = ('status_code', 'display_name')
    ordering = ('status_code',)
