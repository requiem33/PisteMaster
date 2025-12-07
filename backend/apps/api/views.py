# backend/apps/api/views.py
from datetime import timezone

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from .models import Fencer, CompetitionItem, Match
from .serializers import FencerSerializer, CompetitionItemSerializer, MatchSerializer


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


class CompetitionItemViewSet(viewsets.ModelViewSet):
    """
    比赛单项API
    自动支持的端点：
    GET    /api/competition-items/          - 列表
    POST   /api/competition-items/          - 创建新单项
    GET    /api/competition-items/{id}/     - 获取单个单项详情
    PUT    /api/competition-items/{id}/     - 更新单个单项
    PATCH  /api/competition-items/{id}/     - 部分更新单个单项
    DELETE /api/competition-items/{id}/     - 删除单项
    """
    queryset = CompetitionItem.objects.all()
    serializer_class = CompetitionItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['weapon_type', 'gender_category', 'age_group', 'status']
    search_fields = ['name']

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """添加选手到比赛单项"""
        competition_item = self.get_object()

        fencer_id = request.data.get('fencer_id')
        if not fencer_id:
            return Response(
                {'error': '需要提供选手ID'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 导入Fencer模型
        from .models import Fencer

        try:
            fencer = Fencer.objects.get(id=fencer_id)
        except Fencer.DoesNotExist:
            return Response(
                {'error': '选手不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 使用模型的业务方法
        success = competition_item.add_participant(fencer)

        if success:
            return Response({
                'message': f'成功添加选手 {fencer.full_name}',
                'current_participants': competition_item.current_participants
            })
        else:
            return Response(
                {'error': '添加选手失败'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """获取比赛单项的所有选手"""
        competition_item = self.get_object()

        from .serializers import FencerSerializer
        participants = competition_item.participants.all()
        serializer = FencerSerializer(participants, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def matches(self, request, pk=None):
        """获取比赛单项的所有比赛"""
        competition_item = self.get_object()

        matches = competition_item.matches.all()

        # 支持过滤
        match_type = request.query_params.get('match_type')
        status_filter = request.query_params.get('status')

        if match_type:
            matches = matches.filter(match_type=match_type)
        if status_filter:
            matches = matches.filter(status=status_filter)

        serializer = MatchSerializer(matches, many=True)
        return Response(serializer.data)


class MatchViewSet(viewsets.ModelViewSet):
    """
    比赛对阵API
    自动支持的端点：
    GET    /api/matches/          - 列表
    POST   /api/matches/          - 创建新比赛
    GET    /api/matches/{id}/     - 获取单个比赛详情
    PUT    /api/matches/{id}/     - 更新单个比赛
    PATCH  /api/matches/{id}/     - 部分更新单个比赛
    DELETE /api/matches/{id}/     - 删除比赛
    """
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['competition_item', 'match_type', 'status', 'pool_number']
    search_fields = ['fencer_a__last_name', 'fencer_b__last_name']

    def get_queryset(self):
        """优化查询集，减少数据库查询"""
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'fencer_a', 'fencer_b', 'competition_item'
        )
        return queryset

    @action(detail=True, methods=['post'])
    def update_score(self, request, pk=None):
        """更新比赛比分"""
        match = self.get_object()

        score_a = request.data.get('score_a')
        score_b = request.data.get('score_b')

        if score_a is None or score_b is None:
            return Response(
                {'error': '需要提供比分'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 更新比分
        match.score_a = score_a
        match.score_b = score_b

        # 如果比赛完成，更新状态
        if request.data.get('completed', False):
            match.status = Match.MatchStatus.COMPLETED
            match.ended_at = timezone.now()

        match.save()

        serializer = self.get_serializer(match)
        return Response(serializer.data)
