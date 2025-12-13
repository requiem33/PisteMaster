from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import DjangoEvent


@admin.register(DjangoEvent)
class EventAdmin(admin.ModelAdmin):
    """比赛项目管理后台"""

    list_display = (
        'event_name',
        'tournament_link',
        'event_type_display',
        'status_display',
        'start_time',
        'participant_count_display',
        'is_active_display',
        'created_at'
    )

    list_display_links = ('event_name',)

    search_fields = ('event_name', 'tournament__tournament_name')

    list_filter = (
        'tournament',
        'event_type',
        'status',
        'is_team_event',
        'start_time',
        'created_at'
    )

    ordering = ('-start_time', 'event_name')

    list_per_page = 25

    fieldsets = (
        ('基本信息', {
            'fields': ('event_name', 'tournament', 'event_type')
        }),
        ('赛制设置', {
            'fields': ('rule', 'status')
        }),
        ('时间安排', {
            'fields': ('start_time',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('id', 'created_at', 'updated_at', 'is_team_event')

    autocomplete_fields = ['tournament', 'rule', 'event_type', 'status']

    def tournament_link(self, obj):
        """赛事链接"""
        if obj.tournament:
            url = reverse('admin:fencing_organizer_djangotournament_change', args=[obj.tournament.id])
            return format_html('<a href="{}">{}</a>', url, obj.tournament.tournament_name)
        return "-"

    tournament_link.short_description = "赛事"

    def event_type_display(self, obj):
        """项目类型显示"""
        if obj.event_type:
            return obj.event_type.display_name
        return "-"

    event_type_display.short_description = "项目类型"

    def status_display(self, obj):
        """状态显示"""
        if obj.status:
            return obj.status.display_name or obj.status.status_code
        return "-"

    status_display.short_description = "状态"

    def participant_count_display(self, obj):
        """参与者数量显示"""
        return f"{obj.participant_count} 人"

    participant_count_display.short_description = "参与者"

    def is_active_display(self, obj):
        """活跃状态显示"""
        if obj.is_active:
            return format_html('<span style="color: green;">● 活跃</span>')
        return format_html('<span style="color: gray;">○ 非活跃</span>')

    is_active_display.short_description = "活跃状态"

    def get_queryset(self, request):
        """优化查询集"""
        return super().get_queryset(request).select_related(
            'tournament', 'rule', 'event_type', 'status'
        )
