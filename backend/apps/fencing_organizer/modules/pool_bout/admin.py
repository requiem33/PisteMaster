from django.contrib import admin
from django.utils.html import format_html
from .models import DjangoPoolBout


@admin.register(DjangoPoolBout)
class PoolBoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'pool_display', 'fencer_a_display', 'fencer_b_display', 'score_display', 'winner_display',
                    'status_display', 'scheduled_time', 'duration_display')
    list_filter = ('status', 'pool', 'scheduled_time')
    search_fields = ('fencer_a__last_name', 'fencer_a__first_name', 'fencer_b__last_name', 'fencer_b__first_name',
                     'pool__pool_letter')
    ordering = ('pool', 'scheduled_time')
    raw_id_fields = ('pool', 'fencer_a', 'fencer_b', 'winner', 'status')
    readonly_fields = ('created_at', 'updated_at', 'is_completed', 'is_draw', 'is_forfeited', 'is_ready_to_start',
                       'target_score', 'is_score_valid', 'display_name')

    fieldsets = (
        ('基本信息', {
            'fields': ('pool', 'fencer_a', 'fencer_b', 'status', 'winner')
        }),
        ('比分', {
            'fields': ('fencer_a_score', 'fencer_b_score')
        }),
        ('时间', {
            'fields': ('scheduled_time', 'actual_start_time', 'actual_end_time', 'duration_seconds')
        }),
        ('计算字段', {
            'fields': ('is_completed', 'is_draw', 'is_forfeited', 'is_ready_to_start', 'target_score', 'is_score_valid',
                       'display_name')
        }),
        ('其他', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )

    def pool_display(self, obj):
        if obj.pool:
            return f"小组{obj.pool.pool_number}{obj.pool.pool_letter or ''}"
        return '-'

    pool_display.short_description = '小组'

    def fencer_a_display(self, obj):
        if obj.fencer_a:
            return f"{obj.fencer_a.display_name} ({obj.fencer_a.country_code})"
        return '-'

    fencer_a_display.short_description = '运动员A'

    def fencer_b_display(self, obj):
        if obj.fencer_b:
            return f"{obj.fencer_b.display_name} ({obj.fencer_b.country_code})"
        return '-'

    fencer_b_display.short_description = '运动员B'

    def score_display(self, obj):
        if obj.is_completed:
            return f"{obj.fencer_a_score} - {obj.fencer_b_score}"
        return '未开始'

    score_display.short_description = '比分'

    def winner_display(self, obj):
        if obj.winner:
            return f"{obj.winner.display_name} ({obj.winner.country_code})"
        elif obj.is_completed and obj.fencer_a_score == obj.fencer_b_score:
            return '平局'
        return '-'

    winner_display.short_description = '胜者'

    def status_display(self, obj):
        if obj.status:
            status_display = obj.status.status_code
            if obj.status.description:
                status_display += f" ({obj.status.description})"
            return status_display
        return '-'

    status_display.short_description = '状态'

    def duration_display(self, obj):
        if obj.duration_seconds:
            minutes = obj.duration_seconds // 60
            seconds = obj.duration_seconds % 60
            return f"{minutes}:{seconds:02d}"
        return '-'

    duration_display.short_description = '时长'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('pool', 'fencer_a', 'fencer_b', 'winner', 'status')
        return queryset
