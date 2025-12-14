from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import get_object_or_404
from uuid import UUID

from .models import DjangoPoolBout
from .serializers import PoolBoutSerializer, PoolBoutResultSerializer, PoolBoutStartSerializer, \
    PoolBoutGenerateSerializer
from ...services.pool_bout_service import PoolBoutService
from ...services.pool_service import PoolService


class PoolBoutViewSet(viewsets.ModelViewSet):
    """
    PoolBout API视图集
    """
    queryset = DjangoPoolBout.objects.all().order_by('pool', 'scheduled_time')
    serializer_class = PoolBoutSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['pool', 'fencer_a', 'fencer_b', 'status', 'winner']
    search_fields = ['pool__pool_letter', 'fencer_a__last_name', 'fencer_a__first_name', 'fencer_b__last_name',
                     'fencer_b__first_name']
    ordering_fields = ['scheduled_time', 'actual_start_time', 'actual_end_time']
    ordering = ['scheduled_time']

    def get_serializer_class(self):
        if self.action == 'update_result':
            return PoolBoutResultSerializer
        elif self.action == 'start_bout':
            return PoolBoutStartSerializer
        elif self.action == 'generate_round_robin':
            return PoolBoutGenerateSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        # 可以根据用户权限进行过滤
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            bout_service = PoolBoutService()
            bout = bout_service.create_bout(serializer.validated_data)
            django_bout = DjangoPoolBout.objects.get(id=bout.id)
            output_serializer = PoolBoutSerializer(django_bout)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except PoolBoutService.PoolBoutServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            bout_service = PoolBoutService()
            bout = bout_service.update_bout(instance.id, serializer.validated_data)
            django_bout = DjangoPoolBout.objects.get(id=bout.id)
            output_serializer = PoolBoutSerializer(django_bout)
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        except PoolBoutService.PoolBoutServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='update-result')
    def update_result(self, request, pk=None):
        """
        更新比赛结果
        """
        bout = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fencer_a_score = serializer.validated_data['fencer_a_score']
        fencer_b_score = serializer.validated_data['fencer_b_score']
        winner_id = serializer.validated_data.get('winner_id')
        notes = serializer.validated_data.get('notes')

        try:
            bout_service = PoolBoutService()
            updated_bout = bout_service.update_bout_result(bout.id, fencer_a_score, fencer_b_score, winner_id)

            # 更新备注
            if notes:
                updated_bout.notes = notes
                updated_bout.save()

            output_serializer = PoolBoutSerializer(DjangoPoolBout.objects.get(id=updated_bout.id))
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        except PoolBoutService.PoolBoutServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='start')
    def start_bout(self, request, pk=None):
        """
        开始比赛
        """
        bout = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        actual_start_time = serializer.validated_data.get('actual_start_time')
        notes = serializer.validated_data.get('notes')

        try:
            bout_service = PoolBoutService()
            updated_bout = bout_service.start_bout(bout.id)

            # 更新实际开始时间（如果提供）
            if actual_start_time:
                updated_bout.actual_start_time = actual_start_time
                updated_bout.save()

            # 更新备注
            if notes:
                updated_bout.notes = notes
                updated_bout.save()

            output_serializer = PoolBoutSerializer(DjangoPoolBout.objects.get(id=updated_bout.id))
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        except PoolBoutService.PoolBoutServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete_bout(self, request, pk=None):
        """
        完成比赛
        """
        bout = self.get_object()
        serializer = PoolBoutResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fencer_a_score = serializer.validated_data['fencer_a_score']
        fencer_b_score = serializer.validated_data['fencer_b_score']
        winner_id = serializer.validated_data.get('winner_id')
        notes = serializer.validated_data.get('notes')

        try:
            bout_service = PoolBoutService()
            updated_bout = bout_service.complete_bout(bout.id, fencer_a_score, fencer_b_score)

            # 如果指定了胜者，更新胜者
            if winner_id:
                updated_bout.winner_id = winner_id
                updated_bout.save()

            # 更新备注
            if notes:
                updated_bout.notes = notes
                updated_bout.save()

            output_serializer = PoolBoutSerializer(DjangoPoolBout.objects.get(id=updated_bout.id))
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        except PoolBoutService.PoolBoutServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_bout(self, request, pk=None):
        """
        取消比赛
        """
        bout = self.get_object()
        notes = request.data.get('notes')

        try:
            bout_service = PoolBoutService()
            updated_bout = bout_service.cancel_bout(bout.id, notes)
            output_serializer = PoolBoutSerializer(DjangoPoolBout.objects.get(id=updated_bout.id))
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        except PoolBoutService.PoolBoutServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='stats')
    def get_stats(self, request, pk=None):
        """
        获取比赛统计信息
        """
        bout = self.get_object()

        stats = {
            'is_completed': bout.is_completed,
            'is_draw': bout.is_draw,
            'is_forfeited': bout.is_forfeited,
            'is_ready_to_start': bout.is_ready_to_start,
            'target_score': bout.target_score,
            'is_score_valid': bout.is_score_valid,
            'display_name': bout.display_name,
        }

        return Response(stats, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='generate-round-robin')
    def generate_round_robin(self, request):
        """
        为小组生成循环赛对阵
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pool_id = serializer.validated_data['pool_id']

        try:
            bout_service = PoolBoutService()
            bouts = bout_service.generate_round_robin_bouts(pool_id)

            bout_ids = [bout.id for bout in bouts]
            django_bouts = DjangoPoolBout.objects.filter(id__in=bout_ids).order_by('scheduled_time')
            output_serializer = PoolBoutSerializer(django_bouts, many=True)

            return Response({
                "message": f"成功生成{len(bouts)}场比赛",
                "bouts": output_serializer.data
            }, status=status.HTTP_201_CREATED)
        except PoolBoutService.PoolBoutServiceError as e:
            return Response({"detail": str(e), "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='by-pool/(?P<pool_id>[^/.]+)')
    def by_pool(self, request, pool_id=None):
        """
        获取指定小组的所有比赛
        """
        try:
            pool_uuid = UUID(pool_id)
        except ValueError:
            return Response({"detail": "Invalid pool ID format"}, status=status.HTTP_400_BAD_REQUEST)

        bouts = DjangoPoolBout.objects.filter(pool_id=pool_uuid).order_by('scheduled_time')
        serializer = PoolBoutSerializer(bouts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming_bouts(self, request):
        """
        获取即将到来的比赛
        """
        hours = request.query_params.get('hours', 24)
        try:
            hours = int(hours)
        except ValueError:
            hours = 24

        try:
            bout_service = PoolBoutService()
            bouts = bout_service.get_upcoming_bouts(hours)

            bout_ids = [bout.id for bout in bouts]
            django_bouts = DjangoPoolBout.objects.filter(id__in=bout_ids).order_by('scheduled_time')
            output_serializer = PoolBoutSerializer(django_bouts, many=True)

            return Response(output_serializer.data, status=status.HTTP_200_OK)
        except PoolBoutService.PoolBoutServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='active')
    def active_bouts(self, request):
        """
        获取活跃的比赛
        """
        try:
            bout_service = PoolBoutService()
            bouts = bout_service.get_active_bouts()

            bout_ids = [bout.id for bout in bouts]
            django_bouts = DjangoPoolBout.objects.filter(id__in=bout_ids).order_by('scheduled_time')
            output_serializer = PoolBoutSerializer(django_bouts, many=True)

            return Response(output_serializer.data, status=status.HTTP_200_OK)
        except PoolBoutService.PoolBoutServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
