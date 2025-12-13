from django.contrib import admin
from .models import DjangoRankingType


@admin.register(DjangoRankingType)
class RankingTypeAdmin(admin.ModelAdmin):
    """排名类型管理后台"""

    list_display = ('type_code', 'display_name')
    search_fields = ('type_code', 'display_name')
    ordering = ('type_code',)
