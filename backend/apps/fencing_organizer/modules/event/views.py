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
