from django.contrib import admin
from .models import DjangoPool


@admin.register(DjangoPool)
class PoolAdmin(admin.ModelAdmin):
    list_display = ("pool_number", "stage_id", "event_name", "status", "is_completed")
    list_filter = ("status", "is_completed", "event")
    search_fields = ("pool_number", "event__event_name", "stage_id")
    ordering = ("event", "stage_id", "pool_number")
    raw_id_fields = ("event",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("基本信息", {"fields": ("event", "stage_id", "pool_number")}),
        ("状态", {"fields": ("status", "is_completed", "is_locked")}),
        ("数据记录", {"fields": ("fencer_ids", "results", "stats")}),
        ("时间戳", {"fields": ("created_at", "updated_at")}),
    )

    def event_name(self, obj):
        return obj.event.event_name if obj.event else "-"

    event_name.short_description = "项目名称"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("event")
        return queryset
