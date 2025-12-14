from django.contrib import admin
from .models import DjangoPiste


@admin.register(DjangoPiste)
class PisteAdmin(admin.ModelAdmin):
    """淘汰赛类型管理后台"""

    list_display = ('piste_type', 'notes')
    search_fields = ('piste_type', 'notes')
    ordering = ('piste_type',)
