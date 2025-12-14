from django.contrib import admin
from django.utils.html import format_html
from .models import DjangoPool


@admin.register(DjangoPool)
class PoolAdmin(admin.ModelAdmin):
    list_display = ('pool_number', 'pool_letter', 'event_name', 'piste_display', 'status', 'is_completed', 'start_time',
                    'participant_count_display', 'bout_count_display')
    list_filter = ('status', 'is_completed', 'event', 'piste', 'start_time')
    search_fields = ('pool_number', 'pool_letter', 'event__event_name', 'piste__piste_number')
    ordering = ('event', 'pool_number')
    raw_id_fields = ('event', 'piste')
    readonly_fields = ('created_at', 'updated_at', 'participant_count', 'bout_count', 'completed_bout_count',
                       'completion_percentage')

    fieldsets = (
        ('基本信息', {
            'fields': ('event', 'pool_number', 'pool_letter', 'piste', 'start_time')
        }),
        ('状态', {
            'fields': ('status', 'is_completed')
        }),
        ('统计信息', {
            'fields': ('participant_count', 'bout_count', 'completed_bout_count', 'completion_percentage')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def event_name(self, obj):
        return obj.event.event_name if obj.event else '-'

    event_name.short_description = '项目名称'

    def piste_display(self, obj):
        if obj.piste:
            return f"{obj.piste.piste_number} ({obj.piste.location or '无位置'})"
        return '-'

    piste_display.short_description = '剑道'

    def participant_count_display(self, obj):
        return obj.participant_count

    participant_count_display.short_description = '人数'

    def bout_count_display(self, obj):
        return f"{obj.completed_bout_count}/{obj.bout_count}"

    bout_count_display.short_description = '比赛进度'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('event', 'piste')
        return queryset
