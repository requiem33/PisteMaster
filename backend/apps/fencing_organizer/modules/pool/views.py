from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import get_object_or_404
from uuid import UUID

from .models import DjangoPool
from .serializers import PoolSerializer, PoolCreateSerializer, PoolUpdateSerializer, PoolGenerateSerializer
from ...services.pool_service import PoolService


class PoolViewSet(viewsets.ModelViewSet):
    """
    Pool API视图集
    """
    queryset = DjangoPool.objects.all().order_by('event', 'pool_number')
    serializer_class = PoolSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event', 'piste', 'status', 'is_completed']
    search_fields = ['pool_letter', 'event__event_name']
    ordering_fields = ['pool_number', 'start_time', 'created_at']
    ordering = ['pool_number']

    def get_serializer_class(self):
        if self.action == 'create':
            return PoolCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PoolUpdateSerializer
        elif self.action == 'generate_pools':
            return PoolGenerateSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        # 可以根据用户权限进行过滤
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

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_pools(self, request):
        """
        为指定事件生成小组
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event_id = serializer.validated_data['event_id']
        pool_count = serializer.validated_data.get('pool_count', 1)
        piste_id = serializer.validated_data.get('piste_id')

        try:
            pool_service = PoolService()
            pools = pool_service.create_pools_for_event(event_id, pool_count, piste_id)

            # 获取生成的DjangoPool对象
            pool_ids = [pool.id for pool in pools]
            django_pools = DjangoPool.objects.filter(id__in=pool_ids).order_by('pool_number')
            output_serializer = PoolSerializer(django_pools, many=True)

            return Response({
                "message": f"成功生成{len(pools)}个小组",
                "pools": output_serializer.data
            }, status=status.HTTP_201_CREATED)
        except PoolService.PoolServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='generate-balanced')
    def generate_balanced_pools(self, request):
        """
        为指定事件生成平衡小组（考虑种子排名）
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event_id = serializer.validated_data['event_id']
        pool_size = serializer.validated_data.get('pool_size', 7)

        try:
            pool_service = PoolService()
            pools = pool_service.generate_balanced_pools(event_id, pool_size)

            pool_ids = [pool.id for pool in pools]
            django_pools = DjangoPool.objects.filter(id__in=pool_ids).order_by('pool_number')
            output_serializer = PoolSerializer(django_pools, many=True)

            return Response({
                "message": f"成功生成{len(pools)}个平衡小组",
                "pools": output_serializer.data
            }, status=status.HTTP_201_CREATED)
        except PoolService.PoolServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='assign-piste')
    def assign_piste(self, request, pk=None):
        """
        为小组分配剑道
        """
        pool = self.get_object()
        piste_id = request.data.get('piste_id')

        if not piste_id:
            return Response({"detail": "piste_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pool_service = PoolService()
            updated_pool = pool_service.update_pool(pool.id, {'piste_id': piste_id})
            output_serializer = PoolSerializer(DjangoPool.objects.get(id=updated_pool.id))
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        except PoolService.PoolServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        更新小组状态
        """
        pool = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response({"detail": "status is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pool_service = PoolService()
            updated_pool = pool_service.update_pool_status(pool.id, new_status)
            output_serializer = PoolSerializer(DjangoPool.objects.get(id=updated_pool.id))
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        except PoolService.PoolServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='batch-assign-piste')
    def batch_assign_piste(self, request):
        """
        批量分配剑道
        """
        pool_ids = request.data.get('pool_ids', [])
        piste_id = request.data.get('piste_id')

        if not pool_ids:
            return Response({"detail": "pool_ids is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not piste_id:
            return Response({"detail": "piste_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pool_service = PoolService()
            updated_pools = pool_service.assign_piste_to_pools(pool_ids, piste_id)

            updated_pool_ids = [pool.id for pool in updated_pools]
            django_pools = DjangoPool.objects.filter(id__in=updated_pool_ids).order_by('pool_number')
            output_serializer = PoolSerializer(django_pools, many=True)

            return Response({
                "message": f"成功为{len(updated_pools)}个小组分配剑道",
                "pools": output_serializer.data
            }, status=status.HTTP_200_OK)
        except PoolService.PoolServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='batch-schedule')
    def batch_schedule(self, request):
        """
        批量安排小组时间
        """
        pool_ids = request.data.get('pool_ids', [])
        start_time = request.data.get('start_time')
        interval_minutes = request.data.get('interval_minutes', 30)

        if not pool_ids:
            return Response({"detail": "pool_ids is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not start_time:
            return Response({"detail": "start_time is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from datetime import datetime
            start_time_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

            pool_service = PoolService()
            scheduled_pools = pool_service.schedule_pools(pool_ids, start_time_dt, interval_minutes)

            scheduled_pool_ids = [pool.id for pool in scheduled_pools]
            django_pools = DjangoPool.objects.filter(id__in=scheduled_pool_ids).order_by('start_time')
            output_serializer = PoolSerializer(django_pools, many=True)

            return Response({
                "message": f"成功安排{len(scheduled_pools)}个小组的时间",
                "pools": output_serializer.data
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": f"时间格式错误: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except PoolService.PoolServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='stats')
    def get_stats(self, request, pk=None):
        """
        获取小组统计信息
        """
        pool = self.get_object()

        stats = {
            'participant_count': pool.participant_count,
            'bout_count': pool.bout_count,
            'completed_bout_count': pool.completed_bout_count,
            'completion_percentage': pool.completion_percentage,
            'is_active': pool.is_active,
        }

        return Response(stats, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='by-event/(?P<event_id>[^/.]+)')
    def by_event(self, request, event_id=None):
        """
        获取指定事件的所有小组
        """
        try:
            event_uuid = UUID(event_id)
        except ValueError:
            return Response({"detail": "Invalid event ID format"}, status=status.HTTP_400_BAD_REQUEST)

        pools = DjangoPool.objects.filter(event_id=event_uuid).order_by('pool_number')
        serializer = PoolSerializer(pools, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)