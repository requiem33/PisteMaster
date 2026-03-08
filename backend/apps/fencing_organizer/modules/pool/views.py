from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import get_object_or_404
from uuid import UUID

from .models import DjangoPool
from .serializers import PoolSerializer, PoolCreateSerializer, PoolUpdateSerializer
from ...services.pool_service import PoolService


class PoolViewSet(viewsets.ModelViewSet):
    """
    Pool API视图集
    """
    queryset = DjangoPool.objects.all().order_by('event', 'stage_id', 'pool_number')
    serializer_class = PoolSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event', 'stage_id', 'status', 'is_completed']
    search_fields = ['event__event_name']
    ordering_fields = ['pool_number', 'start_time', 'created_at']
    ordering = ['pool_number']

    def get_permissions(self):
        # MVP: allow anonymous
        if self.action in ['list', 'retrieve', 'by_event', 'update_results']:
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return PoolCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PoolUpdateSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            pool_service = PoolService()
            pool = pool_service.create_pool(serializer.validated_data)
            django_pool = DjangoPool.objects.get(id=pool.id)
            output_serializer = PoolSerializer(django_pool)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except PoolService.PoolServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            pool_service = PoolService()
            pool = pool_service.update_pool(instance.id, serializer.validated_data)
            django_pool = DjangoPool.objects.get(id=pool.id)
            output_serializer = PoolSerializer(django_pool)
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        except PoolService.PoolServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='results')
    def update_results(self, request, pk=None):
        """更新单组比赛结果矩阵与统计"""
        pool = self.get_object()
        
        results = request.data.get('results')
        stats = request.data.get('stats')
        is_locked = request.data.get('is_locked')
        
        if results is not None:
            pool.results = results
        if stats is not None:
            pool.stats = stats
        if is_locked is not None:
            pool.is_locked = is_locked
            
        pool.save(update_fields=['results', 'stats', 'is_locked', 'updated_at'])
        
        return Response({
            "message": "更新成功",
            "is_locked": pool.is_locked
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='by-event/(?P<event_id>[^/.]+)')
    def by_event(self, request, event_id=None):
        """
        获取指定事件的所有小组
        """
        try:
            event_uuid = UUID(event_id)
        except ValueError:
            return Response({"detail": "Invalid event ID format"}, status=status.HTTP_400_BAD_REQUEST)

        pools = DjangoPool.objects.filter(event_id=event_uuid).order_by('stage_id', 'pool_number')
        serializer = PoolSerializer(pools, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)