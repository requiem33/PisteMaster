from django.contrib import admin
from django.utils.html import format_html
from .models import DjangoEventParticipant


@admin.register(DjangoEventParticipant)
class EventParticipantAdmin(admin.ModelAdmin):
    """EventParticipant管理后台"""

    list_display = ('fencer_display', 'event_display', 'seed_rank', 'is_confirmed', 'registration_time', 'created_at')
    list_filter = ('is_confirmed', 'event', 'event__tournament', 'fencer__country_code')
    search_fields = ('fencer__first_name', 'fencer__last_name', 'fencer__display_name', 'event__event_name',
                     'event__tournament__tournament_name')
    ordering = ('event', 'seed_rank')
    readonly_fields = ('registration_time', 'created_at', 'updated_at')

    fieldsets = (
        ('基本信息', {
            'fields': ('event', 'fencer')
        }),
        ('种子信息', {
            'fields': ('seed_rank', 'seed_value')
        }),
        ('状态', {
            'fields': ('is_confirmed', 'registration_time', 'notes')
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

    def event_display(self, obj):
        """事件显示"""
        if obj.event:
            return format_html(
                '<a href="/admin/fencing_organizer/djangoevent/{}/change/">{}</a>',
                obj.event.id,
                obj.event.event_name
            )
        return '-'

    event_display.short_description = '项目'

    def get_queryset(self, request):
        """优化查询"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('event', 'fencer', 'event__tournament')
        return queryset
