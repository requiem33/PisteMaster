from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from datetime import date

from .models import DjangoTournament
from .serializers import TournamentSerializer, TournamentCreateSerializer
from backend.apps.fencing_organizer.services.tournament_service import TournamentService
from backend.apps.fencing_organizer.services.tournament_status_service import TournamentStatusService


class TournamentViewSet(viewsets.GenericViewSet):
    """
    赛事 API

    list: 获取赛事列表
    retrieve: 获取单个赛事
    create: 创建赛事
    update: 更新赛事
    partial_update: 部分更新赛事
    destroy: 删除赛事
    update_status: 更新赛事状态
    upcoming: 获取即将到来的赛事
    ongoing: 获取进行中的赛事
    statistics: 获取赛事统计
    """

    queryset = DjangoTournament.objects.all()
    serializer_class = TournamentSerializer
    service = TournamentService()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'start_date', 'end_date']
    search_fields = ['tournament_name', 'organizer', 'location']
    ordering_fields = ['tournament_name', 'start_date', 'end_date', 'created_at']
    ordering = ['-start_date']

    def get_permissions(self):
        """权限控制"""
        # 【临时修改】允许匿名用户创建和列出赛事，以便于开发
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]  # 👈 允许任何人访问

        # 其他需要更高权限的操作，依然保持原样
        if self.action in ['update', 'partial_update', 'destroy', 'update_status']:
            return [IsAuthenticated(), IsAdminUser()]

        return [IsAuthenticated()]

    def get_serializer_class(self):
        """根据action选择序列化器"""
        if self.action == 'create':
            return TournamentCreateSerializer
        return TournamentSerializer

    def list(self, request):
        # 【修改】使用 GenericViewSet 提供的辅助方法，简化代码
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            # 现在 self.get_serializer 是存在的！
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            tournament_entity = self.service.get_tournament_by_id(pk)
            if not tournament_entity:
                return Response({"detail": "赛事不存在"}, status=status.HTTP_404_NOT_FOUND)

            # 使用 self.get_serializer，而不是直接实例化
            serializer = self.get_serializer(tournament_entity)
            return Response(serializer.data)
        except Exception as e:
            # 简化错误处理
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        # get_serializer() 现在由 GenericViewSet 提供，它会自动调用 get_serializer_class()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            tournament_entity = self.service.create_tournament(serializer.validated_data)

            # 【最佳实践】创建成功后，应该返回一个带有 Location header 的 201 响应
            # 为了获取完整的对象用于响应，我们再次序列化 entity
            # 注意：Serializer 需要能处理 entity 或 model
            response_serializer = TournamentSerializer(tournament_entity)  # 假设 Serializer 可以处理 entity

            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except self.service.TournamentServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"服务器内部错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        """更新赛事"""
        # 验证数据
        serializer = self.get_serializer(data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        try:
            # 将serializer数据转换为service需要的格式
            tournament_data = serializer.validated_data
            if 'status' in tournament_data:
                tournament_data['status_id'] = tournament_data['status'].id

            tournament = self.service.update_tournament(pk, tournament_data)

            # 获取更新后的Django对象
            django_tournament = DjangoTournament.objects.select_related('status').get(id=tournament.id)
            response_serializer = self.get_serializer(django_tournament)

            return Response(response_serializer.data)

        except TournamentService.TournamentServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    def partial_update(self, request, pk=None):
        """部分更新赛事"""
        # 对于部分更新，使用通用的serializer
        serializer = self.serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            tournament_data = serializer.validated_data
            if 'status' in tournament_data:
                tournament_data['status_id'] = tournament_data['status'].id

            tournament = self.service.update_tournament(pk, tournament_data)

            django_tournament = DjangoTournament.objects.select_related('status').get(id=tournament.id)
            response_serializer = self.serializer_class(django_tournament)

            return Response(response_serializer.data)

        except TournamentService.TournamentServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, pk=None):
        """删除赛事"""
        try:
            success = self.service.delete_tournament(pk)

            if not success:
                return Response(
                    {"detail": "赛事不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

        except TournamentService.TournamentServiceError as e:
            return Response(
                {"detail": e.message},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """更新赛事状态"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            status_id = serializer.validated_data['status_id']
            tournament = self.service.update_tournament_status(pk, status_id)

            # 获取更新后的Django对象
            django_tournament = DjangoTournament.objects.select_related('status').get(id=tournament.id)
            response_serializer = self.serializer_class(django_tournament)

            return Response(response_serializer.data)

        except TournamentService.TournamentServiceError as e:
            return Response(
                {"detail": e.message},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """获取即将到来的赛事"""
        days = int(request.query_params.get('days', 30))

        tournaments = self.service.get_upcoming_tournaments(days)

        # 转换为Django模型用于序列化
        tournament_ids = [t.id for t in tournaments]
        django_tournaments = DjangoTournament.objects.select_related('status').filter(
            id__in=tournament_ids
        )

        serializer = self.get_serializer(django_tournaments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def ongoing(self, request):
        """获取进行中的赛事"""
        tournaments = self.service.get_ongoing_tournaments()

        # 转换为Django模型用于序列化
        tournament_ids = [t.id for t in tournaments]
        django_tournaments = DjangoTournament.objects.select_related('status').filter(
            id__in=tournament_ids
        )

        serializer = self.get_serializer(django_tournaments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取赛事统计"""
        from django.db.models import Count, Q

        # 基础统计
        total_tournaments = DjangoTournament.objects.count()

        # 按状态统计
        status_stats = DjangoTournament.objects.values(
            'status__status_code', 'status__display_name'
        ).annotate(count=Count('id')).order_by('status__status_code')

        # 时间统计
        today = date.today()
        upcoming_count = DjangoTournament.objects.filter(start_date__gte=today).count()
        ongoing_count = DjangoTournament.objects.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today)
        ).count()
        past_count = DjangoTournament.objects.filter(end_date__lt=today).count()

        return Response({
            "total_tournaments": total_tournaments,
            "upcoming_count": upcoming_count,
            "ongoing_count": ongoing_count,
            "past_count": past_count,
            "status_distribution": list(status_stats),
            "date_range": {
                "today": today.isoformat(),
                "upcoming_days": 30  # 默认值
            }
        })

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """获取赛事时间线（状态变更历史）"""
        # 这里可以集成审计日志或专门的状态变更记录
        # MVP版本可以先返回基本信息

        try:
            tournament = DjangoTournament.objects.select_related('status').get(id=pk)

            return Response({
                "tournament_id": pk,
                "current_status": {
                    "code": tournament.status.status_code,
                    "display_name": tournament.status.display_name,
                    "since": tournament.updated_at.isoformat()
                },
                "created_at": tournament.created_at.isoformat(),
                "last_updated": tournament.updated_at.isoformat()
            })

        except DjangoTournament.DoesNotExist:
            return Response(
                {"detail": "赛事不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
