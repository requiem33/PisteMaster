from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import get_object_or_404
from uuid import UUID

from .models import DjangoFencer
from .serializers import (
    FencerSerializer,
    FencerCreateSerializer,
    FencerUpdateSerializer,
    FencerSearchSerializer
)
from ...services.fencer_service import FencerService


class StandardPagination(PageNumberPagination):
    """标准分页器"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class FencerViewSet(viewsets.ModelViewSet):
    """
    Fencer API视图集

    list:
    获取运动员列表

    create:
    创建新运动员

    retrieve:
    获取运动员详情

    update:
    更新运动员信息

    partial_update:
    部分更新运动员信息

    destroy:
    删除运动员
    """
    queryset = DjangoFencer.objects.all().order_by('last_name', 'first_name')
    serializer_class = FencerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'country_code', 'primary_weapon']
    search_fields = ['first_name', 'last_name', 'display_name', 'fencing_id']
    ordering_fields = ['last_name', 'first_name', 'current_ranking', 'created_at', 'updated_at']
    ordering = ['last_name', 'first_name']
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return FencerCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return FencerUpdateSerializer
        elif self.action == 'search':
            return FencerSearchSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        """根据不同动作设置权限"""
        if self.action in ['list', 'retrieve', 'search']:
            return [AllowAny()]  # 允许匿名用户查看
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            fencer_service = FencerService()
            fencer = fencer_service.create_fencer(serializer.validated_data)
            django_fencer = DjangoFencer.objects.get(id=fencer.id)
            output_serializer = self.get_serializer(django_fencer)

            headers = self.get_success_headers(output_serializer.data)
            return Response(
                output_serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except FencerService.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            fencer_service = FencerService()
            fencer = fencer_service.update_fencer(instance.id, serializer.validated_data)
            django_fencer = DjangoFencer.objects.get(id=fencer.id)
            output_serializer = self.get_serializer(django_fencer)
            return Response(output_serializer.data)
        except FencerService.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        try:
            fencer_service = FencerService()
            success = fencer_service.delete_fencer(instance.id)

            if success:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {"detail": "删除失败"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except FencerService.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], url_path='search')
    def search(self, request):
        """
        搜索运动员
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data['query']
        limit = serializer.validated_data.get('limit', 50)

        try:
            fencer_service = FencerService()
            fencers = fencer_service.search_fencers(query, limit)

            # 获取对应的Django模型实例
            fencer_ids = [fencer.id for fencer in fencers]
            django_fencers = DjangoFencer.objects.filter(id__in=fencer_ids)

            output_serializer = FencerSerializer(django_fencers, many=True)
            return Response({
                "query": query,
                "count": len(fencers),
                "results": output_serializer.data
            })
        except FencerService.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='by-country/(?P<country_code>[^/.]+)')
    def by_country(self, request, country_code=None):
        """
        根据国家获取运动员列表
        """
        try:
            fencer_service = FencerService()
            fencers = fencer_service.get_fencers_by_country(country_code)

            fencer_ids = [fencer.id for fencer in fencers]
            django_fencers = DjangoFencer.objects.filter(id__in=fencer_ids)

            serializer = self.get_serializer(django_fencers, many=True)
            return Response({
                "country_code": country_code,
                "count": len(fencers),
                "results": serializer.data
            })
        except FencerService.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='by-weapon/(?P<weapon>[^/.]+)')
    def by_weapon(self, request, weapon=None):
        """
        根据剑种获取运动员列表
        """
        try:
            fencer_service = FencerService()
            fencers = fencer_service.get_fencers_by_weapon(weapon)

            fencer_ids = [fencer.id for fencer in fencers]
            django_fencers = DjangoFencer.objects.filter(id__in=fencer_ids)

            serializer = self.get_serializer(django_fencers, many=True)
            return Response({
                "weapon": weapon,
                "count": len(fencers),
                "results": serializer.data
            })
        except FencerService.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        获取运动员统计信息
        """
        try:
            fencer_service = FencerService()
            statistics = fencer_service.get_statistics()
            return Response(statistics)
        except FencerService.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='top-ranked')
    def top_ranked(self, request):
        """
        获取排名最高的运动员
        """
        limit = int(request.query_params.get('limit', 100))
        country = request.query_params.get('country')

        fencer_service = FencerService()
        fencers = fencer_service.repository.get_top_ranked_fencers(limit, country)

        fencer_ids = [fencer.id for fencer in fencers]
        django_fencers = DjangoFencer.objects.filter(id__in=fencer_ids)

        serializer = self.get_serializer(django_fencers, many=True)
        return Response({
            "limit": limit,
            "country": country,
            "count": len(fencers),
            "results": serializer.data
        })
