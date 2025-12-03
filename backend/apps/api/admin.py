from django.contrib import admin

# 正确地从 models.py 中导入之前定义的 Fencer Django模型
from .models import Fencer

# 方式一：使用装饰器进行注册（推荐，更简洁）
@admin.register(Fencer)
class FencerAdmin(admin.ModelAdmin):
    # 在后台列表页显示的字段
    list_display = ('last_name', 'first_name', 'country', 'club', 'weapon', 'status', 'rating')
    # 设置右侧的筛选器
    list_filter = ('country', 'weapon', 'status')
    # 设置顶部搜索框可搜索的字段
    search_fields = ('last_name', 'first_name', 'club')
