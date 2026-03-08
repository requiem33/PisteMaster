from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import DjangoEvent
from .serializers import EventSerializer, EventCreateSerializer
from ...services.event_service import EventService
from ..tournament.models import DjangoTournament


class EventViewSet(viewsets.GenericViewSet):
    """
    比赛项目 API
    """

    queryset = DjangoEvent.objects.all()
    serializer_class = EventSerializer
    service = EventService()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tournament', 'event_type', 'status', 'is_team_event']
    search_fields = ['event_name', 'tournament__tournament_name']
    ordering_fields = ['event_name', 'start_time', 'created_at']
    ordering = ['start_time']

    def get_permissions(self):
        """权限控制"""
        # MVP开发允许任何人访问
        if self.action in ['create', 'list', 'retrieve', 'update', 'partial_update', 'destroy', 'by_tournament', 'update_live_ranking']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return EventCreateSerializer
        return EventSerializer

    def list(self, request):
        """获取项目列表"""
        queryset = self.filter_queryset(self.get_queryset())
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
                return Response({"detail": "项目不存在"}, status=status.HTTP_404_NOT_FOUND)
            
            django_event = DjangoEvent.objects.get(id=event.id)
            serializer = self.get_serializer(django_event)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        """创建项目"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            event_data = serializer.validated_data
            event = self.service.create_event(event_data)
            
            django_event = DjangoEvent.objects.get(id=event.id)
            response_serializer = EventSerializer(django_event)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except self.service.EventServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"创建失败: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        """更新项目"""
        serializer = EventSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            event_data = serializer.validated_data
            event = self.service.update_event(pk, event_data)
            
            django_event = DjangoEvent.objects.get(id=event.id)
            response_serializer = EventSerializer(django_event)
            return Response(response_serializer.data)
        except self.service.EventServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """删除项目"""
        try:
            success = self.service.delete_event(pk)
            if not success:
                return Response({"detail": "项目不存在"}, status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except self.service.EventServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['put'], url_path='live-ranking')
    def update_live_ranking(self, request, pk=None):
        """初始化/全量更新实时排名"""
        live_ranking = request.data.get('live_ranking')
        if live_ranking is None:
            return Response({"detail": "live_ranking parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            event = self.service.update_event(pk, {'live_ranking': live_ranking})
            django_event = DjangoEvent.objects.get(id=event.id)
            serializer = EventSerializer(django_event)
            return Response(serializer.data)
        except self.service.EventServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='participants')
    def get_participants(self, request, pk=None):
        """获取项目参与者列表"""
        event = self.get_object()
        
        from backend.apps.fencing_organizer.modules.event_participant.serializers import EventParticipantSerializer
        from backend.apps.fencing_organizer.modules.event_participant.models import DjangoEventParticipant

        # 查询该项目下的所有关联名单，联表查询 fencer 信息
        django_participants = DjangoEventParticipant.objects.filter(event=event).select_related('fencer')
        serializer = EventParticipantSerializer(django_participants, many=True)

        return Response({
            "event_id": str(event.id),
            "event_name": event.event_name,
            "participant_count": django_participants.count(),
            "participants": serializer.data
        })

    @action(detail=True, methods=['put'], url_path='participants/sync')
    def sync_participants(self, request, pk=None):
        """覆盖式同步项目参赛名单"""
        event = self.get_object()
        fencer_ids = request.data.get('fencer_ids')
        
        if not isinstance(fencer_ids, list):
            return Response({"detail": "fencer_ids must be a list"}, status=status.HTTP_400_BAD_REQUEST)
            
        from backend.apps.fencing_organizer.modules.event_participant.models import DjangoEventParticipant
        from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
        from django.db import transaction
        
        try:
            with transaction.atomic():
                # 删除原有所有名单
                DjangoEventParticipant.objects.filter(event=event).delete()
                
                # 过滤出真实存在的运动员
                valid_fencers = DjangoFencer.objects.filter(id__in=fencer_ids)
                valid_fencer_ids = [f.id for f in valid_fencers]
                
                # 批量创建新名单
                new_participants = [
                    DjangoEventParticipant(event=event, fencer_id=f_id)
                    for f_id in valid_fencer_ids
                ]
                DjangoEventParticipant.objects.bulk_create(new_participants)
                
            return Response({
                "message": f"成功同步了 {len(valid_fencer_ids)} 名参赛者",
                "synced_count": len(valid_fencer_ids)
            })
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post', 'get'], url_path='stages/(?P<stage_id>[^/.]+)/pools')
    def stage_pools(self, request, pk=None, stage_id=None):
        """批量保存或获取某阶段分组"""
        event = self.get_object()
        from backend.apps.fencing_organizer.modules.pool.models import DjangoPool
        
        if request.method == 'GET':
            pools = DjangoPool.objects.filter(event=event, stage_id=stage_id).order_by('pool_number')
            from backend.apps.fencing_organizer.modules.pool.serializers import PoolSerializer
            return Response(PoolSerializer(pools, many=True).data)
            
        elif request.method == 'POST':
            pools_data = request.data
            if not isinstance(pools_data, list):
                return Response({"detail": "Expected a list of pools"}, status=status.HTTP_400_BAD_REQUEST)
                
            from django.db import transaction
            try:
                with transaction.atomic():
                    # 删除该阶段原有的所有小组
                    DjangoPool.objects.filter(event=event, stage_id=stage_id).delete()
                    
                    # 批量创建新小组
                    new_pools = []
                    for p_data in pools_data:
                        new_pools.append(DjangoPool(
                            event=event,
                            stage_id=stage_id,
                            pool_number=p_data.get('pool_number'),
                            fencer_ids=p_data.get('fencer_ids', [])
                        ))
                    
                    DjangoPool.objects.bulk_create(new_pools)
                    
                return Response({"message": f"成功保存 {len(new_pools)} 个小组到阶段 {stage_id}"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['put', 'get'], url_path='stages/(?P<stage_id>[^/.]+)/detree')
    def stage_detree(self, request, pk=None, stage_id=None):
        """保存或获取某阶段淘汰赛对阵图"""
        event = self.get_object()
        
        if request.method == 'GET':
            tree_data = event.de_trees.get(stage_id)
            return Response(tree_data if tree_data else [])
            
        elif request.method == 'PUT':
            tree_data = request.data.get('tree_data')
            if tree_data is None:
                # 兼容直接传数组的情况
                if isinstance(request.data, list):
                    tree_data = request.data
                else:
                    return Response({"detail": "tree_data is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 更新 JSON
            current_trees = dict(event.de_trees) if event.de_trees else {}
            current_trees[stage_id] = tree_data
            
            # 存库
            event.de_trees = current_trees
            event.save(update_fields=['de_trees'])
            
            return Response({"message": "保存成功"})
