from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import DjangoFencer


@admin.register(DjangoFencer)
class FencerAdmin(admin.ModelAdmin):
    """Fencer管理后台"""

    list_display = ('display_name', 'country_display', 'primary_weapon_display',
                    'current_ranking', 'fencing_id', 'age_display', 'created_at')
    list_filter = ('gender', 'country_code', 'primary_weapon')
    search_fields = ('first_name', 'last_name', 'display_name', 'fencing_id', 'country_code')
    ordering = ('last_name', 'first_name')
    readonly_fields = ('created_at', 'updated_at', 'age_display', 'is_international')
    fieldsets = (
        ('基本信息', {
            'fields': ('first_name', 'last_name', 'display_name')
        }),
        ('个人信息', {
            'fields': ('gender', 'country_code', 'birth_date')
        }),
        ('击剑信息', {
            'fields': ('fencing_id', 'current_ranking', 'primary_weapon')
        }),
        ('计算字段', {
            'fields': ('age_display', 'is_international')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def country_display(self, obj):
        """国家显示"""
        if obj.country_code:
            return format_html(
                '<span class="fi fi-{}"></span> {}',
                obj.country_code.lower(),
                obj.country_code
            )
        return '-'

    country_display.short_description = '国家'
    country_display.admin_order_field = 'country_code'

    def primary_weapon_display(self, obj):
        """剑种显示"""
        if obj.primary_weapon:
            weapon_dict = {
                'FOIL': '🎯 花剑',
                'EPEE': '⚔️ 重剑',
                'SABRE': '⚡ 佩剑'
            }
            return weapon_dict.get(obj.primary_weapon, obj.primary_weapon)
        return '-'

    primary_weapon_display.short_description = '主剑种'
    primary_weapon_display.admin_order_field = 'primary_weapon'

    def age_display(self, obj):
        """年龄显示"""
        if obj.age is not None:
            return f"{obj.age}岁"
        return '-'

    age_display.short_description = '年龄'

    def get_queryset(self, request):
        """优化查询"""
        queryset = super().get_queryset(request)
        return queryset

    class Media:
        """添加CSS样式"""
        css = {
            'all': ['https://cdnjs.cloudflare.com/ajax/libs/flag-icon-css/6.6.6/css/flag-icons.min.css']
        }
