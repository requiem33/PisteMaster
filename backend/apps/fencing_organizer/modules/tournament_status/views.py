from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import DjangoTournamentStatus
from .serializers import TournamentStatusSerializer
from ...services.tournament_status_service import TournamentStatusService


class TournamentStatusViewSet(viewsets.ViewSet):
    """
    赛事状态 API

    list: 获取所有状态
    retrieve: 获取单个状态
    create: 创建新状态
    update: 更新状态
    destroy: 删除状态
    initialize: 初始化预定义状态
    """

    serializer_class = TournamentStatusSerializer
    service = TournamentStatusService()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status_code']
    search_fields = ['status_code', 'display_name', 'description']

    def get_permissions(self):
        """权限控制"""
        if self.action in ['create', 'update', 'destroy', 'initialize']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def list(self, request):
        """获取所有状态列表"""
        statuses = self.service.get_all_statuses()

        # 转换为Django模型用于序列化
        status_ids = [status.id for status in statuses]
        django_statuses = DjangoTournamentStatus.objects.filter(id__in=status_ids)

        # 过滤和搜索
        for backend in list(self.filter_backends):
            django_statuses = backend().filter_queryset(self.request, django_statuses, self)

        serializer = self.serializer_class(django_statuses, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """获取单个状态"""
        try:
            status = self.service.get_status_by_id(pk)
            if not status:
                return Response(
                    {"detail": "状态不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )

            django_status = DjangoTournamentStatus.objects.get(id=status.id)
            serializer = self.serializer_class(django_status)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request):
        """创建新状态"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            status = self.service.create_status(serializer.validated_data)
            django_status = DjangoTournamentStatus.objects.get(id=status.id)
            response_serializer = self.serializer_class(django_status)

            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except TournamentStatusService.TournamentStatusServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"创建失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, pk=None):
        """更新状态"""
        # 验证数据
        serializer = self.serializer_class(data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        try:
            status = self.service.update_status(pk, serializer.validated_data)
            django_status = DjangoTournamentStatus.objects.get(id=status.id)
            response_serializer = self.serializer_class(django_status)

            return Response(response_serializer.data)

        except TournamentStatusService.TournamentStatusServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, pk=None):
        """删除状态"""
        try:
            # 检查是否可以删除（例如是否有赛事使用此状态）
            from ..tournament.models import DjangoTournament
            used_count = DjangoTournament.objects.filter(status_id=pk).count()

            if used_count > 0:
                return Response(
                    {"detail": f"无法删除，有 {used_count} 个赛事正在使用此状态"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 删除状态
            count, _ = DjangoTournamentStatus.objects.filter(id=pk).delete()

            if count == 0:
                return Response(
                    {"detail": "状态不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def initialize(self, request):
        """初始化预定义状态"""
        try:
            created_statuses = self.service.initialize_predefined_statuses()

            return Response({
                "success": True,
                "message": f"成功初始化 {len(created_statuses)} 个状态",
                "created_count": len(created_statuses)
            })

        except Exception as e:
            return Response(
                {"detail": f"初始化失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
