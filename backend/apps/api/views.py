# backend/apps/api/views.py
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Fencer
from .serializers import FencerSerializer


class FencerViewSet(viewsets.ModelViewSet):
    """
    提供 Fencer 模型的完整 CRUD API 接口。
    自动支持的端点：
    GET    /api/fencers/          - 列表（支持搜索、过滤、分页）
    POST   /api/fencers/          - 创建新选手
    GET    /api/fencers/{id}/     - 获取单个选手详情
    PUT    /api/fencers/{id}/     - 更新单个选手（全字段）
    PATCH  /api/fencers/{id}/     - 部分更新单个选手
    DELETE /api/fencers/{id}/     - 删除选手
    """
    queryset = Fencer.objects.all().order_by('last_name', 'first_name')
    serializer_class = FencerSerializer

    # 配置过滤、搜索和排序后端（按需启用）
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # 可过滤字段（精确匹配）
    filterset_fields = ['country', 'weapon', 'status', 'gender']

    # 可搜索字段（模糊搜索）
    search_fields = ['last_name', 'first_name', 'club', 'region']

    # 可排序字段
    ordering_fields = ['last_name', 'first_name', 'rating', 'seed', 'created_at']
    ordering = ['last_name', 'first_name']  # 默认排序