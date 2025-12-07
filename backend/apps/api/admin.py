from django.contrib import admin

# 正确地从 models.py 中导入之前定义的 Fencer Django模型
from .models import Fencer, CompetitionRules, Match


# 方式一：使用装饰器进行注册（推荐，更简洁）
@admin.register(Fencer)
class FencerAdmin(admin.ModelAdmin):
    # 在后台列表页显示的字段
    list_display = ('last_name', 'first_name', 'country', 'club', 'weapon', 'status', 'rating')
    # 设置右侧的筛选器
    list_filter = ('country', 'weapon', 'status')
    # 设置顶部搜索框可搜索的字段
    search_fields = ('last_name', 'first_name', 'club')


@admin.register(CompetitionRules)
class CompetitionRulesAdmin(admin.ModelAdmin):
    list_display = ('name', 'weapon_type', 'is_default', 'created_at')
    list_filter = ('weapon_type', 'is_default')
    search_fields = ('name',)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_fencers', 'competition_item', 'match_type', 'status', 'scheduled_time')
    list_filter = ('match_type', 'status', 'competition_item')
    search_fields = ('fencer_a__last_name', 'fencer_b__last_name', 'competition_item__name')
    list_select_related = ('fencer_a', 'fencer_b', 'competition_item')

    def get_fencers(self, obj):
        fencer_a_name = "轮空" if not obj.fencer_a else obj.fencer_a.full_name
        fencer_b_name = "轮空" if not obj.fencer_b else obj.fencer_b.full_name
        return f"{fencer_a_name} vs {fencer_b_name}"

    get_fencers.short_description = '对阵'

    # 简化表单，便于快速测试
    fieldsets = (
        ('基本信息', {
            'fields': ('competition_item', 'match_type', 'status')
        }),
        ('对阵选手', {
            'fields': ('fencer_a', 'fencer_b')
        }),
        ('比分', {
            'fields': ('score_a', 'score_b')
        }),
        ('时间场地', {
            'fields': ('scheduled_time', 'piste_number')
        }),
    )
