from django.contrib import admin
from django.utils.html import format_html
from .models import DjangoRule


@admin.register(DjangoRule)
class RuleAdmin(admin.ModelAdmin):
    """赛制规则管理后台"""

    list_display = (
        'rule_name',
        'elimination_type_display',
        'final_ranking_type_display',
        'pool_size',
        'match_score_pool',
        'match_score_elimination',
        'total_qualified_count',
        'created_at'
    )

    list_display_links = ('rule_name',)

    search_fields = ('rule_name', 'description', 'match_format')

    list_filter = (
        'elimination_type',
        'final_ranking_type',
        'pool_size'
    )

    ordering = ('rule_name',)

    list_per_page = 25

    fieldsets = (
        ('基本信息', {
            'fields': ('rule_name', 'description')
        }),
        ('赛制设置', {
            'fields': ('elimination_type', 'final_ranking_type', 'total_qualified_count')
        }),
        ('小组赛设置', {
            'fields': ('pool_size', 'match_score_pool', 'group_qualification_ratio')
        }),
        ('淘汰赛设置', {
            'fields': ('match_score_elimination',)
        }),
        ('比赛格式', {
            'fields': ('match_format', 'match_duration')
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('id', 'created_at', 'updated_at')

    autocomplete_fields = ['elimination_type', 'final_ranking_type']

    def elimination_type_display(self, obj):
        """淘汰赛类型显示"""
        return obj.elimination_type.display_name or obj.elimination_type.type_code

    elimination_type_display.short_description = "淘汰赛类型"

    def final_ranking_type_display(self, obj):
        """排名类型显示"""
        return obj.final_ranking_type.display_name or obj.final_ranking_type.type_code

    final_ranking_type_display.short_description = "排名类型"

    def get_queryset(self, request):
        """优化查询集"""
        return super().get_queryset(request).select_related(
            'elimination_type', 'final_ranking_type'
        )
