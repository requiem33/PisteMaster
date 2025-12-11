from django.contrib import admin
from .models import DjangoFencer


@admin.register(DjangoFencer)
class FencerAdmin(admin.ModelAdmin):
    """Fencer模型的Django后台管理配置"""

    # 列表页面显示的字段
    list_display = (
        'last_name',
        'first_name',
        'display_name',
        'gender',
        'country_code',
        'fencing_id',
        'current_ranking',
        'primary_weapon',
        'created_at',
        'updated_at'
    )

    # 列表页面可点击进入详情的字段
    list_display_links = ('last_name', 'first_name')

    # 列表页面的搜索框，搜索的字段
    search_fields = (
        'first_name',
        'last_name',
        'display_name',
        'fencing_id',
        'country_code'
    )

    # 列表页面的过滤器，可过滤的字段
    list_filter = (
        'gender',
        'country_code',
        'primary_weapon',
        'created_at',
        'updated_at'
    )

    # 列表页面的排序方式
    ordering = ('last_name', 'first_name')

    # 列表页面每页显示的记录数
    list_per_page = 25

    # 详情页面的字段布局
    fieldsets = (
        ('基本信息', {
            'fields': ('first_name', 'last_name', 'display_name', 'gender', 'birth_date')
        }),
        ('击剑信息', {
            'fields': ('fencing_id', 'current_ranking', 'primary_weapon')
        }),
        ('国家信息', {
            'fields': ('country_code',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # 可折叠的字段集
        }),
    )

    # 只读字段（在详情页面不可编辑）
    readonly_fields = ('id', 'created_at', 'updated_at')

    # 日期层次结构（在列表页面顶部显示日期筛选器）
    date_hierarchy = 'created_at'
