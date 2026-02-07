from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import DjangoTournament


@admin.register(DjangoTournament)
class TournamentAdmin(admin.ModelAdmin):
    """赛事管理后台"""

    list_display = (
        'tournament_name',
        'organizer',
        'location',
        'start_date',
        'end_date',
        'status',
        'duration_days_display',
        'created_at'
    )

    list_display_links = ('tournament_name',)

    search_fields = ('tournament_name', 'organizer', 'location')

    list_filter = (
        'status',
        'start_date',
        'end_date',
        'created_at'
    )

    ordering = ('-start_date', 'tournament_name')

    list_per_page = 25

    fieldsets = (
        ('基本信息', {
            'fields': ('tournament_name', 'organizer', 'location')
        }),
        ('时间信息', {
            'fields': ('start_date', 'end_date')
        }),
        ('状态管理', {
            'fields': ('status',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('id', 'created_at', 'updated_at', 'duration_days_display')

    def duration_days_display(self, obj):
        """持续时间显示"""
        return f"{obj.duration_days} 天"

    duration_days_display.short_description = "持续天数"

    def get_readonly_fields(self, request, obj=None):
        """编辑时保护某些字段"""
        readonly = list(self.readonly_fields)
        if obj:  # 编辑现有对象时
            # 可以添加更多只读字段
            pass
        return readonly

    def get_queryset(self, request):
        """优化查询集"""
        return super().get_queryset(request)
