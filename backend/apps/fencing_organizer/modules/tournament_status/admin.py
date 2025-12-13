from django.contrib import admin
from .models import DjangoTournamentStatus


@admin.register(DjangoTournamentStatus)
class TournamentStatusAdmin(admin.ModelAdmin):
    """赛事状态管理后台"""

    list_display = ('status_code', 'display_name', 'description', 'created_at', 'updated_at')
    list_display_links = ('status_code', 'display_name')
    search_fields = ('status_code', 'display_name', 'description')
    list_filter = ('created_at', 'updated_at')
    ordering = ('status_code',)
    list_per_page = 20

    fieldsets = (
        ('基本信息', {
            'fields': ('status_code', 'display_name', 'description')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('id', 'created_at', 'updated_at')

    def get_readonly_fields(self, request, obj=None):
        """编辑时保护某些字段"""
        if obj:  # 编辑现有对象时
            return self.readonly_fields + ('status_code',)
        return self.readonly_fields