from django.contrib import admin
from django.utils.html import format_html
from .models import DjangoPoolAssignment


@admin.register(DjangoPoolAssignment)
class PoolAssignmentAdmin(admin.ModelAdmin):
    """PoolAssignment管理后台"""

    list_display = ('fencer_display', 'pool_display', 'final_pool_rank', 'is_qualified',
                    'victories_display', 'indicator_display', 'touches_scored', 'touches_received',
                    'matches_played', 'created_at')
    list_filter = ('is_qualified', 'pool', 'pool__event', 'pool__event__tournament')
    search_fields = ('fencer__first_name', 'fencer__last_name', 'fencer__display_name',
                     'pool__pool_letter', 'pool__event__event_name')
    ordering = ('pool', 'final_pool_rank')
    readonly_fields = ('indicator', 'created_at', 'updated_at', 'win_rate',
                       'average_touches_scored', 'average_touches_received')

    fieldsets = (
        ('基本信息', {
            'fields': ('pool', 'fencer')
        }),
        ('排名', {
            'fields': ('final_pool_rank', 'is_qualified', 'qualification_rank')
        }),
        ('比赛数据', {
            'fields': ('victories', 'touches_scored', 'touches_received', 'matches_played')
        }),
        ('计算字段', {
            'fields': ('indicator', 'win_rate', 'average_touches_scored', 'average_touches_received')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def fencer_display(self, obj):
        """运动员显示"""
        if obj.fencer:
            return format_html(
                '<a href="/admin/fencing_organizer/djangofencer/{}/change/">{}</a>',
                obj.fencer.id,
                f"{obj.fencer.display_name} ({obj.fencer.country_code})"
            )
        return '-'

    fencer_display.short_description = '运动员'

    def pool_display(self, obj):
        """小组显示"""
        if obj.pool:
            event_name = obj.pool.event.event_name if obj.pool.event else '未知项目'
            return format_html(
                '<a href="/admin/fencing_organizer/djangopool/{}/change/">小组{}{}</a><br><small>{}</small>',
                obj.pool.id,
                obj.pool.pool_number,
                obj.pool.pool_letter or '',
                event_name
            )
        return '-'

    pool_display.short_description = '小组'

    def victories_display(self, obj):
        """胜场显示"""
        return f"{obj.victories}/{obj.matches_played}"

    victories_display.short_description = '胜/总'

    def indicator_display(self, obj):
        """得失分差显示"""
        if obj.indicator > 0:
            return format_html('<span style="color: green;">+{}</span>', obj.indicator)
        elif obj.indicator < 0:
            return format_html('<span style="color: red;">{}</span>', obj.indicator)
        return obj.indicator

    indicator_display.short_description = '得失分差'

    def get_queryset(self, request):
        """优化查询"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('pool', 'fencer', 'pool__event', 'pool__event__tournament')
        return queryset
