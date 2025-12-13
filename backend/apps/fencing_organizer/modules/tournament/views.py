from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from datetime import date

from .models import DjangoTournament
from .serializers import TournamentSerializer, TournamentCreateSerializer, TournamentStatusUpdateSerializer
from backend.apps.fencing_organizer.services.tournament_service import TournamentService
from backend.apps.fencing_organizer.services.tournament_status_service import TournamentStatusService


class TournamentViewSet(viewsets.ViewSet):
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

    serializer_class = TournamentSerializer
    service = TournamentService()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'start_date', 'end_date']
    search_fields = ['tournament_name', 'organizer', 'location']
    ordering_fields = ['tournament_name', 'start_date', 'end_date', 'created_at']
    ordering = ['-start_date']

    def get_permissions(self):
        """权限控制"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'update_status']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """根据action选择序列化器"""
        if self.action == 'create':
            return TournamentCreateSerializer
        elif self.action == 'update_status':
            return TournamentStatusUpdateSerializer
        return TournamentSerializer

    def list(self, request):
        """获取赛事列表"""
        # 获取过滤后的queryset
        queryset = DjangoTournament.objects.select_related('status').all()

        # 应用过滤、搜索、排序
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)

        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """获取单个赛事"""
        try:
            tournament = self.service.get_tournament_by_id(pk)
            if not tournament:
                return Response(
                    {"detail": "赛事不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )

            django_tournament = DjangoTournament.objects.select_related('status').get(id=tournament.id)

            # 添加统计信息
            django_tournament.event_count = django_tournament.events.count()  # 如果有related_name

            serializer = self.get_serializer(django_tournament)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request):
        """创建赛事"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # 将serializer数据转换为service需要的格式
            tournament_data = serializer.validated_data
            tournament_data['status_id'] = tournament_data['status'].id

            tournament = self.service.create_tournament(tournament_data)

            # 获取完整的Django对象用于序列化
            django_tournament = DjangoTournament.objects.select_related('status').get(id=tournament.id)
            response_serializer = self.get_serializer(django_tournament)

            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except TournamentService.TournamentServiceError as e:
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
