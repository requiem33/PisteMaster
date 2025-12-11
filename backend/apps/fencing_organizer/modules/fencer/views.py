from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import DjangoFencer
from .serializers import FencerSerializer


class FencerViewSet(viewsets.ModelViewSet):
    """Fencer模型的视图集，提供标准的CRUD操作"""
    queryset = DjangoFencer.objects.all()
    serializer_class = FencerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # 过滤字段
    filterset_fields = ['gender', 'country_code', 'primary_weapon']

    # 搜索字段
    search_fields = ['first_name', 'last_name', 'display_name', 'fencing_id']

    # 排序字段
    ordering_fields = ['last_name', 'first_name', 'created_at', 'updated_at', 'current_ranking']

    # 默认排序
    ordering = ['last_name', 'first_name']
