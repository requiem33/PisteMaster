from django.contrib import admin
from django.utils.html import format_html
from .models import DjangoEventType


@admin.register(DjangoEventType)
class EventTypeAdmin(admin.ModelAdmin):
    """项目类型管理后台"""

    list_display = ('type_code', 'display_name', 'weapon_type', 'gender', 'is_individual_display')
    list_filter = ('weapon_type', 'gender')
    search_fields = ('type_code', 'display_name')
    ordering = ('type_code',)

    def is_individual_display(self, obj):
        """是否为个人赛显示"""
        if obj.is_individual:
            return format_html('<span style="color: green;">● 个人赛</span>')
        else:
            return format_html('<span style="color: blue;">● 团体赛</span>')

    is_individual_display.short_description = "赛制类型"
