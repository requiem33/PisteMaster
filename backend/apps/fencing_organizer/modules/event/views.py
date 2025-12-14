from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta

from .models import DjangoEvent
from .serializers import EventSerializer
from ...services.event_service import EventService
from ..tournament.models import DjangoTournament
from ..event_type.models import DjangoEventType
from ..event_status.models import DjangoEventStatus


class EventViewSet(viewsets.ViewSet):
    """
    比赛项目 API

    list: 获取项目列表
    retrieve: 获取单个项目
    create: 创建项目
    update: 更新项目
    destroy: 删除项目
    update_status: 更新项目状态
    by_tournament: 按赛事获取项目
    upcoming: 获取即将到来的项目
    active: 获取活跃项目
    """

    serializer_class = EventSerializer
    service = EventService()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tournament', 'event_type', 'status', 'is_team_event']
    search_fields = ['event_name', 'tournament__tournament_name']
    ordering_fields = ['event_name', 'start_time', 'created_at']
    ordering = ['start_time']

    def get_permissions(self):
        """权限控制"""
        if self.action in ['create', 'update', 'destroy', 'update_status']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def list(self, request):
        """获取项目列表"""
        # 获取过滤后的queryset
        queryset = DjangoEvent.objects.select_related(
            'tournament', 'rule', 'event_type', 'status'
        ).all()

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
        """获取单个项目"""
        try:
            event = self.service.get_event_by_id(pk)
            if not event:
                return Response(
                    {"detail": "项目不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )

            django_event = DjangoEvent.objects.select_related(
                'tournament', 'rule', 'event_type', 'status'
            ).get(id=event.id)

            serializer = self.get_serializer(django_event)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request):
        """创建项目"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # 将serializer数据转换为service需要的格式
            event_data = {
                'tournament_id': serializer.validated_data['tournament'].id,
                'rule_id': serializer.validated_data['rule'].id,
                'event_type_id': serializer.validated_data['event_type'].id,
                'status_id': serializer.validated_data['status'].id,
                'event_name': serializer.validated_data['event_name'],
                'is_team_event': serializer.validated_data['is_team_event'],
                'start_time': serializer.validated_data.get('start_time')
            }

            event = self.service.create_event(event_data)

            # 获取完整的Django对象用于序列化
            django_event = DjangoEvent.objects.select_related(
                'tournament', 'rule', 'event_type', 'status'
            ).get(id=event.id)

            response_serializer = self.get_serializer(django_event)

            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except EventService.EventServiceError as e:
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
        """更新项目"""
        serializer = self.get_serializer(data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        try:
            # 准备数据
            event_data = {}

            if 'tournament' in serializer.validated_data:
                event_data['tournament_id'] = serializer.validated_data['tournament'].id

            if 'rule' in serializer.validated_data:
                event_data['rule_id'] = serializer.validated_data['rule'].id

            if 'event_type' in serializer.validated_data:
                event_data['event_type_id'] = serializer.validated_data['event_type'].id

            if 'status' in serializer.validated_data:
                event_data['status_id'] = serializer.validated_data['status'].id

            if 'event_name' in serializer.validated_data:
                event_data['event_name'] = serializer.validated_data['event_name']

            if 'start_time' in serializer.validated_data:
                event_data['start_time'] = serializer.validated_data['start_time']

            # 只有提供了event_type才设置is_team_event
            if 'event_type' in serializer.validated_data:
                event_data['is_team_event'] = serializer.validated_data['event_type'].is_team

            event = self.service.update_event(pk, event_data)

            # 获取更新后的Django对象
            django_event = DjangoEvent.objects.select_related(
                'tournament', 'rule', 'event_type', 'status'
            ).get(id=event.id)

            response_serializer = self.get_serializer(django_event)

            return Response(response_serializer.data)

        except EventService.EventServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, pk=None):
        """删除项目"""
        try:
            success = self.service.delete_event(pk)

            if not success:
                return Response(
                    {"detail": "项目不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

        except EventService.EventServiceError as e:
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
        """更新项目状态"""
        status_id = request.data.get('status_id')

        if not status_id:
            return Response(
                {"detail": "status_id 参数必填"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            event = self.service.update_event_status(pk, status_id)

            # 获取更新后的Django对象
            django_event = DjangoEvent.objects.select_related(
                'tournament', 'rule', 'event_type', 'status'
            ).get(id=event.id)

            serializer = self.get_serializer(django_event)
            return Response(serializer.data)

        except EventService.EventServiceError as e:
            return Response(
                {"detail": e.message},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def by_tournament(self, request):
        """按赛事获取项目"""
        tournament_id = request.query_params.get('tournament_id')

        if not tournament_id:
            return Response(
                {"detail": "tournament_id 参数必填"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            events = self.service.get_events_by_tournament(tournament_id)

            # 转换为Django模型用于序列化
            event_ids = [event.id for event in events]
            django_events = DjangoEvent.objects.select_related(
                'tournament', 'rule', 'event_type', 'status'
            ).filter(id__in=event_ids)

            serializer = self.get_serializer(django_events, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """获取即将到来的项目"""
        days = int(request.query_params.get('days', 7))

        events = self.service.get_upcoming_events(days)

        # 转换为Django模型用于序列化
        event_ids = [event.id for event in events]
        django_events = DjangoEvent.objects.select_related(
            'tournament', 'rule', 'event_type', 'status'
        ).filter(id__in=event_ids)

        serializer = self.get_serializer(django_events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """获取活跃项目"""
        events = self.service.get_active_events()

        # 转换为Django模型用于序列化
        event_ids = [event.id for event in events]
        django_events = DjangoEvent.objects.select_related(
            'tournament', 'rule', 'event_type', 'status'
        ).filter(id__in=event_ids)

        # 应用过滤
        for backend in list(self.filter_backends):
            django_events = backend().filter_queryset(self.request, django_events, self)

        serializer = self.get_serializer(django_events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """搜索项目"""
        filters = {}

        # 收集过滤条件
        if 'tournament_id' in request.query_params:
            filters['tournament_id'] = request.query_params['tournament_id']
        if 'tournament_name' in request.query_params:
            filters['tournament_name'] = request.query_params['tournament_name']
        if 'event_name' in request.query_params:
            filters['event_name'] = request.query_params['event_name']
        if 'event_type_code' in request.query_params:
            filters['event_type_code'] = request.query_params['event_type_code']
        if 'status_code' in request.query_params:
            filters['status_code'] = request.query_params['status_code']
        if 'weapon_type' in request.query_params:
            filters['weapon_type'] = request.query_params['weapon_type']
        if 'gender' in request.query_params:
            filters['gender'] = request.query_params['gender']
        if 'is_team_event' in request.query_params:
            filters['is_team_event'] = request.query_params['is_team_event'].lower() == 'true'
        if 'is_active' in request.query_params:
            filters['is_active'] = request.query_params['is_active'].lower() == 'true'
        if 'ordering' in request.query_params:
            filters['ordering'] = request.query_params['ordering']

        # 调用Service层搜索
        events = self.service.search_events(**filters)

        # 转换为Django模型用于序列化
        event_ids = [event.id for event in events]
        django_events = DjangoEvent.objects.select_related(
            'tournament', 'rule', 'event_type', 'status'
        ).filter(id__in=event_ids)

        serializer = self.get_serializer(django_events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取项目统计"""
        from django.db.models import Count, Q

        # 基础统计
        total_events = DjangoEvent.objects.count()

        # 按状态统计
        status_stats = DjangoEvent.objects.values(
            'status__status_code', 'status__display_name'
        ).annotate(count=Count('id')).order_by('status__status_code')

        # 按类型统计
        type_stats = DjangoEvent.objects.values(
            'event_type__display_name', 'event_type__weapon_type'
        ).annotate(count=Count('id')).order_by('event_type__display_name')

        # 按团体/个人统计
        individual_count = DjangoEvent.objects.filter(is_team_event=False).count()
        team_count = DjangoEvent.objects.filter(is_team_event=True).count()

        # 活跃项目统计
        active_events = DjangoEvent.objects.exclude(
            status__status_code='COMPLETED'
        ).exclude(
            status__status_code='CANCELLED'
        ).count()

        return Response({
            "total_events": total_events,
            "individual_count": individual_count,
            "team_count": team_count,
            "active_events": active_events,
            "status_distribution": list(status_stats),
            "type_distribution": list(type_stats)
        })

    @action(detail=False, methods=['post'])
    def initialize(self, request):
        """初始化预定义数据"""
        try:
            results = self.service.initialize_predefined_data()

            return Response({
                "success": True,
                "message": "预定义数据初始化完成",
                "results": results
            })

        except Exception as e:
            return Response(
                {"detail": f"初始化失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='register-fencer')
    def register_fencer(self, request, pk=None):
        """注册运动员到项目"""
        event = self.get_object()
        fencer_id = request.data.get('fencer_id')

        if not fencer_id:
            return Response({"detail": "fencer_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            participant_service = EventParticipantService()
            participant = participant_service.register_fencer_to_event(event.id, fencer_id)

            # 返回参与者信息
            from backend.apps.fencing_organizer.modules.event_participant.serializers import EventParticipantSerializer
            from backend.apps.fencing_organizer.modules.event_participant.models import DjangoEventParticipant

            django_participant = DjangoEventParticipant.objects.get(id=participant.id)
            serializer = EventParticipantSerializer(django_participant)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except EventParticipantService.EventParticipantServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='bulk-register-fencers')
    def bulk_register_fencers(self, request, pk=None):
        """批量注册运动员"""
        event = self.get_object()
        fencer_ids = request.data.get('fencer_ids', [])

        if not fencer_ids:
            return Response({"detail": "fencer_ids is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            participant_service = EventParticipantService()
            successful, failed = participant_service.bulk_register_fencers(event.id, fencer_ids)

            return Response({
                "successful_count": len(successful),
                "failed_count": len(failed),
                "failed_ids": failed,
                "message": f"成功注册 {len(successful)} 名运动员，失败 {len(failed)} 名"
            }, status=status.HTTP_201_CREATED)
        except EventParticipantService.EventParticipantServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='participants')
    def get_participants(self, request, pk=None):
        """获取项目参与者列表"""
        event = self.get_object()
        confirmed_only = request.query_params.get('confirmed_only', 'true').lower() == 'true'

        participant_service = EventParticipantService()
        participants = participant_service.get_event_participants(event.id, confirmed_only)

        from backend.apps.fencing_organizer.modules.event_participant.serializers import EventParticipantSerializer
        from backend.apps.fencing_organizer.modules.event_participant.models import DjangoEventParticipant

        participant_ids = [p.id for p in participants]
        django_participants = DjangoEventParticipant.objects.filter(id__in=participant_ids).select_related('fencer')
        serializer = EventParticipantSerializer(django_participants, many=True)

        return Response({
            "event_id": str(event.id),
            "event_name": event.event_name,
            "participant_count": len(participants),
            "participants": serializer.data
        })

    @action(detail=True, methods=['post'], url_path='generate-pools')
    def generate_pools(self, request, pk=None):
        """为项目生成小组并分配运动员"""
        event = self.get_object()
        pool_size = request.data.get('pool_size', 7)
        group_method = request.data.get('group_method', 'random')  # 'random', 'seeded'

        try:
            pool_service = PoolService()
            pools, assignments = pool_service.generate_pools_with_assignments(event.id, pool_size, group_method)

            from backend.apps.fencing_organizer.modules.pool.serializers import PoolSerializer
            from backend.apps.fencing_organizer.modules.pool.models import DjangoPool
            from backend.apps.fencing_organizer.modules.pool_assignment.serializers import PoolAssignmentSerializer
            from backend.apps.fencing_organizer.modules.pool_assignment.models import DjangoPoolAssignment

            # 获取生成的Django对象
            pool_ids = [pool.id for pool in pools]
            django_pools = DjangoPool.objects.filter(id__in=pool_ids)

            assignment_ids = [assignment.id for assignment in assignments]
            django_assignments = DjangoPoolAssignment.objects.filter(id__in=assignment_ids)

            pool_serializer = PoolSerializer(django_pools, many=True)
            assignment_serializer = PoolAssignmentSerializer(django_assignments, many=True)

            return Response({
                "message": f"成功生成 {len(pools)} 个小组，分配了 {len(assignments)} 名运动员",
                "pools": pool_serializer.data,
                "assignments": assignment_serializer.data
            }, status=status.HTTP_201_CREATED)
        except PoolService.PoolServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)
