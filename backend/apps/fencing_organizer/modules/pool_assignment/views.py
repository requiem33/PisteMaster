# backend/apps/fencing_organizer/modules/pool_assignment/views.py
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import get_object_or_404
from uuid import UUID

from .models import DjangoPoolAssignment
from .serializers import (
    PoolAssignmentSerializer,
    PoolAssignmentCreateSerializer,
    PoolAssignmentUpdateSerializer,
    PoolAssignmentMatchResultSerializer,
    PoolAssignmentBulkCreateSerializer,
    PoolAssignmentRankingUpdateSerializer
)
from ...services.pool_assignment_service import PoolAssignmentService
from ...services.pool_service import PoolService


class StandardPagination(PageNumberPagination):
    """标准分页器"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PoolAssignmentViewSet(viewsets.ModelViewSet):
    """
    PoolAssignment API视图集
    """
    queryset = DjangoPoolAssignment.objects.all().order_by('pool', 'final_pool_rank')
    serializer_class = PoolAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['pool', 'fencer', 'is_qualified']
    search_fields = ['fencer__first_name', 'fencer__last_name', 'fencer__display_name']
    ordering_fields = ['final_pool_rank', 'victories', 'indicator', 'touches_scored', 'touches_received']
    ordering = ['pool', 'final_pool_rank']
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return PoolAssignmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PoolAssignmentUpdateSerializer
        elif self.action == 'update_match_result':
            return PoolAssignmentMatchResultSerializer
        elif self.action == 'bulk_create':
            return PoolAssignmentBulkCreateSerializer
        elif self.action == 'update_ranking':
            return PoolAssignmentRankingUpdateSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        """根据不同动作设置权限"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]  # 允许匿名用户查看
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pool_id = serializer.validated_data['pool'].id
        fencer_id = serializer.validated_data['fencer'].id

        try:
            assignment_service = PoolAssignmentService()
            assignment = assignment_service.create_assignment(pool_id, fencer_id)
            django_assignment = DjangoPoolAssignment.objects.get(id=assignment.id)
            output_serializer = PoolAssignmentSerializer(django_assignment)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except PoolAssignmentService.PoolAssignmentServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # 不允许更新pool和fencer
        if 'pool' in serializer.validated_data or 'fencer' in serializer.validated_data:
            return Response({"detail": "不能修改小组或运动员"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 更新其他字段
            for key, value in serializer.validated_data.items():
                setattr(instance, key, value)
            instance.save()

            output_serializer = PoolAssignmentSerializer(instance)
            return Response(output_serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='update-match-result')
    def update_match_result(self, request, pk=None):
        """更新比赛结果"""
        assignment = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        touches_scored = serializer.validated_data['touches_scored']
        touches_received = serializer.validated_data['touches_received']
        is_winner = serializer.validated_data['is_winner']

        try:
            assignment_service = PoolAssignmentService()
            updated_assignment = assignment_service.update_match_result(
                assignment.pool.id, assignment.fencer.id, touches_scored, touches_received, is_winner
            )

            if updated_assignment:
                output_serializer = PoolAssignmentSerializer(
                    DjangoPoolAssignment.objects.get(id=updated_assignment.id)
                )
                return Response(output_serializer.data)
            else:
                return Response({"detail": "更新比赛结果失败"}, status=status.HTTP_400_BAD_REQUEST)
        except PoolAssignmentService.PoolAssignmentServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create(self, request):
        """批量创建分配记录"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pool_id = request.data.get('pool_id')
        fencer_ids = serializer.validated_data['fencer_ids']

        if not pool_id:
            return Response({"detail": "pool_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assignment_service = PoolAssignmentService()
            assignments = assignment_service.assign_fencers_to_pool(pool_id, fencer_ids)

            assignment_ids = [a.id for a in assignments]
            django_assignments = DjangoPoolAssignment.objects.filter(id__in=assignment_ids)
            output_serializer = PoolAssignmentSerializer(django_assignments, many=True)

            return Response({
                "pool_id": pool_id,
                "created_count": len(assignments),
                "assignments": output_serializer.data
            }, status=status.HTTP_201_CREATED)
        except PoolAssignmentService.PoolAssignmentServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='update-ranking')
    def update_ranking(self, request):
        """批量更新排名"""
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        pool_id = request.data.get('pool_id')
        if not pool_id:
            return Response({"detail": "pool_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        ranking_updates = []
        for update in serializer.validated_data:
            ranking_updates.append({
                'fencer_id': update['fencer_id'],
                'final_pool_rank': update['final_pool_rank'],
                'is_qualified': update['is_qualified'],
                'qualification_rank': update.get('qualification_rank')
            })

        try:
            from ....repositories.pool_assignment_repo import DjangoPoolAssignmentRepository
            assignment_repo = DjangoPoolAssignmentRepository()
            updated_assignments = assignment_repo.update_ranking(pool_id, ranking_updates)

            updated_assignment_ids = [a.id for a in updated_assignments]
            django_assignments = DjangoPoolAssignment.objects.filter(id__in=updated_assignment_ids)
            output_serializer = PoolAssignmentSerializer(django_assignments, many=True)

            return Response({
                "message": f"成功更新 {len(updated_assignments)} 名运动员的排名",
                "assignments": output_serializer.data
            })
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='by-pool/(?P<pool_id>[^/.]+)')
    def by_pool(self, request, pool_id=None):
        """获取指定小组的分配记录"""
        try:
            pool_uuid = UUID(pool_id)
        except ValueError:
            return Response({"detail": "Invalid pool ID format"}, status=status.HTTP_400_BAD_REQUEST)

        assignment_service = PoolAssignmentService()
        assignments = assignment_service.get_assignments_by_pool(pool_uuid)

        assignment_ids = [a.id for a in assignments]
        django_assignments = DjangoPoolAssignment.objects.filter(id__in=assignment_ids)
        serializer = PoolAssignmentSerializer(django_assignments, many=True)

        return Response({
            "pool_id": pool_id,
            "assignment_count": len(assignments),
            "assignments": serializer.data
        })

    @action(detail=False, methods=['get'], url_path='by-fencer/(?P<fencer_id>[^/.]+)')
    def by_fencer(self, request, fencer_id=None):
        """获取指定运动员的小组分配记录"""
        try:
            fencer_uuid = UUID(fencer_id)
        except ValueError:
            return Response({"detail": "Invalid fencer ID format"}, status=status.HTTP_400_BAD_REQUEST)

        assignment_service = PoolAssignmentService()
        assignments = assignment_service.get_assignments_by_fencer(fencer_uuid)

        assignment_ids = [a.id for a in assignments]
        django_assignments = DjangoPoolAssignment.objects.filter(id__in=assignment_ids)
        serializer = PoolAssignmentSerializer(django_assignments, many=True)

        return Response({
            "fencer_id": fencer_id,
            "assignment_count": len(assignments),
            "assignments": serializer.data
        })

    @action(detail=False, methods=['post'], url_path='calculate-pool-ranking/(?P<pool_id>[^/.]+)')
    def calculate_pool_ranking(self, request, pool_id=None):
        """计算小组排名"""
        try:
            pool_uuid = UUID(pool_id)
        except ValueError:
            return Response({"detail": "Invalid pool ID format"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assignment_service = PoolAssignmentService()
            assignments = assignment_service.get_pool_ranking(pool_uuid)

            assignment_ids = [a.id for a in assignments]
            django_assignments = DjangoPoolAssignment.objects.filter(id__in=assignment_ids)
            serializer = PoolAssignmentSerializer(django_assignments, many=True)

            return Response({
                "pool_id": pool_id,
                "ranking": serializer.data
            })
        except PoolAssignmentService.PoolAssignmentServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='calculate-qualification/(?P<event_id>[^/.]+)')
    def calculate_qualification(self, request, event_id=None):
        """计算晋级排名"""
        qualification_count = request.data.get('qualification_count', 16)

        try:
            assignment_service = PoolAssignmentService()
            assignments = assignment_service.calculate_qualification_for_event(event_id, qualification_count)

            assignment_ids = [a.id for a in assignments]
            django_assignments = DjangoPoolAssignment.objects.filter(id__in=assignment_ids)
            serializer = PoolAssignmentSerializer(django_assignments, many=True)

            return Response({
                "event_id": event_id,
                "qualification_count": qualification_count,
                "qualified_fencers": serializer.data
            })
        except PoolAssignmentService.PoolAssignmentServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='qualified/(?P<event_id>[^/.]+)')
    def get_qualified_fencers(self, request, event_id=None):
        """获取晋级运动员"""
        try:
            assignment_service = PoolAssignmentService()
            assignments = assignment_service.get_qualified_fencers_for_event(event_id)

            assignment_ids = [a.id for a in assignments]
            django_assignments = DjangoPoolAssignment.objects.filter(id__in=assignment_ids)
            serializer = PoolAssignmentSerializer(django_assignments, many=True)

            return Response({
                "event_id": event_id,
                "qualified_count": len(assignments),
                "qualified_fencers": serializer.data
            })
        except PoolAssignmentService.PoolAssignmentServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='details/(?P<pool_id>[^/.]+)')
    def get_assignment_details(self, request, pool_id=None):
        """获取分配详情"""
        try:
            pool_uuid = UUID(pool_id)
        except ValueError:
            return Response({"detail": "Invalid pool ID format"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assignment_service = PoolAssignmentService()
            details = assignment_service.get_pool_assignment_details(pool_uuid)

            return Response({
                "pool_id": pool_id,
                "assignment_count": len(details),
                "assignments": details
            })
        except PoolAssignmentService.PoolAssignmentServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='reset/(?P<pool_id>[^/.]+)')
    def reset_assignments(self, request, pool_id=None):
        """重置小组分配"""
        try:
            pool_uuid = UUID(pool_id)
        except ValueError:
            return Response({"detail": "Invalid pool ID format"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assignment_service = PoolAssignmentService()
            success = assignment_service.reset_pool_assignments(pool_uuid)

            if success:
                return Response({
                    "message": f"成功重置小组 {pool_id} 的分配记录"
                })
            else:
                return Response({"detail": "重置失败"}, status=status.HTTP_400_BAD_REQUEST)
        except PoolAssignmentService.PoolAssignmentServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)
