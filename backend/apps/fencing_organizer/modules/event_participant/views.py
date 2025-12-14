from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import get_object_or_404
from uuid import UUID

from .models import DjangoEventParticipant
from .serializers import (
    EventParticipantSerializer,
    EventParticipantCreateSerializer,
    EventParticipantUpdateSerializer,
    EventParticipantBulkRegisterSerializer,
    EventParticipantSeedUpdateSerializer
)
from ...services.event_participant_service import EventParticipantService
from ...services.event_service import EventService
from ...services.fencer_service import FencerService


class StandardPagination(PageNumberPagination):
    """标准分页器"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class EventParticipantViewSet(viewsets.ModelViewSet):
    """
    EventParticipant API视图集
    """
    queryset = DjangoEventParticipant.objects.all().order_by('event', 'seed_rank')
    serializer_class = EventParticipantSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event', 'fencer', 'is_confirmed']
    search_fields = ['fencer__first_name', 'fencer__last_name', 'fencer__display_name', 'event__event_name']
    ordering_fields = ['seed_rank', 'registration_time', 'created_at', 'updated_at']
    ordering = ['event', 'seed_rank']
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return EventParticipantCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EventParticipantUpdateSerializer
        elif self.action == 'bulk_register':
            return EventParticipantBulkRegisterSerializer
        elif self.action == 'update_seeds':
            return EventParticipantSeedUpdateSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        """根据不同动作设置权限"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]  # 允许匿名用户查看
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event_id = serializer.validated_data['event'].id
        fencer_id = serializer.validated_data['fencer'].id
        seed_rank = serializer.validated_data.get('seed_rank')
        seed_value = serializer.validated_data.get('seed_value')
        notes = serializer.validated_data.get('notes')

        try:
            participant_service = EventParticipantService()
            participant = participant_service.register_fencer_to_event(
                event_id, fencer_id, seed_rank, seed_value, notes
            )
            django_participant = DjangoEventParticipant.objects.get(id=participant.id)
            output_serializer = EventParticipantSerializer(django_participant)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except EventParticipantService.EventParticipantServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # 不允许更新event和fencer
        if 'event' in serializer.validated_data or 'fencer' in serializer.validated_data:
            return Response({"detail": "不能修改事件或运动员"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 更新其他字段
            for key, value in serializer.validated_data.items():
                setattr(instance, key, value)
            instance.save()

            output_serializer = EventParticipantSerializer(instance)
            return Response(output_serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='bulk-register')
    def bulk_register(self, request):
        """批量注册运动员到事件"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event_id = request.data.get('event_id')
        fencer_ids = serializer.validated_data['fencer_ids']

        if not event_id:
            return Response({"detail": "event_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            participant_service = EventParticipantService()
            successful, failed = participant_service.bulk_register_fencers(event_id, fencer_ids)

            return Response({
                "event_id": event_id,
                "successful_count": len(successful),
                "failed_count": len(failed),
                "failed_fencer_ids": failed,
                "message": f"成功注册 {len(successful)} 名运动员，失败 {len(failed)} 名"
            }, status=status.HTTP_201_CREATED)
        except EventParticipantService.EventParticipantServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm_participation(self, request, pk=None):
        """确认参赛"""
        participant = self.get_object()

        try:
            participant_service = EventParticipantService()
            updated_participant = participant_service.confirm_participation(participant.event.id, participant.fencer.id)

            if updated_participant:
                output_serializer = EventParticipantSerializer(
                    DjangoEventParticipant.objects.get(id=updated_participant.id))
                return Response(output_serializer.data)
            else:
                return Response({"detail": "确认失败"}, status=status.HTTP_400_BAD_REQUEST)
        except EventParticipantService.EventParticipantServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='unconfirm')
    def unconfirm_participation(self, request, pk=None):
        """取消确认参赛"""
        participant = self.get_object()

        try:
            participant_service = EventParticipantService()
            updated_participant = participant_service.unconfirm_participation(participant.event.id,
                                                                              participant.fencer.id)

            if updated_participant:
                output_serializer = EventParticipantSerializer(
                    DjangoEventParticipant.objects.get(id=updated_participant.id))
                return Response(output_serializer.data)
            else:
                return Response({"detail": "取消确认失败"}, status=status.HTTP_400_BAD_REQUEST)
        except EventParticipantService.EventParticipantServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='update-seeds')
    def update_seeds(self, request):
        """批量更新种子排名"""
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        event_id = request.data.get('event_id')
        if not event_id:
            return Response({"detail": "event_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        seed_updates = []
        for update in serializer.validated_data:
            seed_updates.append({
                'fencer_id': update['fencer_id'],
                'seed_rank': update['seed_rank'],
                'seed_value': update.get('seed_value')
            })

        try:
            participant_service = EventParticipantService()
            updated_participants = participant_service.update_seed_ranking(event_id, seed_updates)

            updated_participant_ids = [p.id for p in updated_participants]
            django_participants = DjangoEventParticipant.objects.filter(id__in=updated_participant_ids)
            output_serializer = EventParticipantSerializer(django_participants, many=True)

            return Response({
                "message": f"成功更新 {len(updated_participants)} 名运动员的种子排名",
                "participants": output_serializer.data
            })
        except EventParticipantService.EventParticipantServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='by-event/(?P<event_id>[^/.]+)')
    def by_event(self, request, event_id=None):
        """获取指定事件的参与者"""
        try:
            event_uuid = UUID(event_id)
        except ValueError:
            return Response({"detail": "Invalid event ID format"}, status=status.HTTP_400_BAD_REQUEST)

        confirmed_only = request.query_params.get('confirmed_only', 'true').lower() == 'true'

        participant_service = EventParticipantService()
        participants = participant_service.get_event_participants(event_uuid, confirmed_only)

        participant_ids = [p.id for p in participants]
        django_participants = DjangoEventParticipant.objects.filter(id__in=participant_ids)
        serializer = EventParticipantSerializer(django_participants, many=True)

        return Response({
            "event_id": event_id,
            "participant_count": len(participants),
            "participants": serializer.data
        })

    @action(detail=False, methods=['get'], url_path='by-fencer/(?P<fencer_id>[^/.]+)')
    def by_fencer(self, request, fencer_id=None):
        """获取指定运动员的参与记录"""
        try:
            fencer_uuid = UUID(fencer_id)
        except ValueError:
            return Response({"detail": "Invalid fencer ID format"}, status=status.HTTP_400_BAD_REQUEST)

        participant_service = EventParticipantService()
        participants = participant_service.get_fencer_events(fencer_uuid)

        participant_ids = [p.id for p in participants]
        django_participants = DjangoEventParticipant.objects.filter(id__in=participant_ids)
        serializer = EventParticipantSerializer(django_participants, many=True)

        return Response({
            "fencer_id": fencer_id,
            "event_count": len(participants),
            "events": serializer.data
        })

    @action(detail=False, methods=['get'], url_path='stats/(?P<event_id>[^/.]+)')
    def event_stats(self, request, event_id=None):
        """获取事件统计信息"""
        try:
            event_uuid = UUID(event_id)
        except ValueError:
            return Response({"detail": "Invalid event ID format"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            participant_service = EventParticipantService()
            stats = participant_service.get_event_stats(event_uuid)
            return Response(stats)
        except EventParticipantService.EventParticipantServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='generate-seeds')
    def generate_seeds(self, request):
        """生成种子排名"""
        event_id = request.data.get('event_id')
        based_on = request.data.get('based_on', 'world_ranking')

        if not event_id:
            return Response({"detail": "event_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            participant_service = EventParticipantService()
            participants = participant_service.generate_seed_ranking(event_id, based_on)

            participant_ids = [p.id for p in participants]
            django_participants = DjangoEventParticipant.objects.filter(id__in=participant_ids)
            serializer = EventParticipantSerializer(django_participants, many=True)

            return Response({
                "message": f"成功为 {len(participants)} 名运动员生成种子排名",
                "based_on": based_on,
                "participants": serializer.data
            })
        except EventParticipantService.EventParticipantServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)