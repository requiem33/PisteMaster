from django.contrib import admin
from .models import DjangoEliminationType


@admin.register(DjangoEliminationType)
class EliminationTypeAdmin(admin.ModelAdmin):
    """淘汰赛类型管理后台"""

    list_display = ('type_code', 'display_name')
    search_fields = ('type_code', 'display_name')
    ordering = ('type_code',)
