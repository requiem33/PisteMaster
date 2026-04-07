from datetime import datetime
from uuid import UUID

from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from backend.apps.fencing_organizer.viewsets.base import SyncWriteModelViewSet
from backend.apps.fencing_organizer.modules.event.models import DjangoEvent
from backend.apps.fencing_organizer.modules.event_participant.models import DjangoEventParticipant
from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
from backend.apps.fencing_organizer.modules.pool.models import DjangoPool
from backend.apps.fencing_organizer.permissions import IsEventEditor
from backend.apps.fencing_organizer.services.event_service import EventService
from backend.apps.fencing_organizer.utils.pagination import get_paginated_response
from .serializers import EventSerializer, EventCreateSerializer


class EventViewSet(SyncWriteModelViewSet):
    """
    Event API - Clean Architecture Implementation

    All operations go through Service layer.
    Service returns Domain models (dataclasses).
    Serializer handles Domain model serialization via DomainModelSerializer.
    """

    sync_table_name = "event"
    queryset = DjangoEvent.objects.all()
    serializer_class = EventSerializer
    service = EventService()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["tournament", "event_type", "status", "is_team_event"]
    search_fields = ["event_name", "tournament__tournament_name"]
    ordering_fields = ["event_name", "start_time", "created_at"]
    ordering = ["start_time"]

    def get_permissions(self):
        if self.action in ["list", "retrieve", "by_tournament", "get_participants"]:
            return [AllowAny()]
        elif self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "update_live_ranking",
            "sync_participants",
            "stage_pools",
            "stage_detree",
        ]:
            return [IsEventEditor()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return EventCreateSerializer
        return EventSerializer

    def list(self, request):
        events = self.service.get_all_events()

        tournament_id = request.query_params.get("tournament")
        if tournament_id:
            try:
                tournament_uuid = UUID(tournament_id)
                events = [e for e in events if e.tournament_id == tournament_uuid]
            except (ValueError, TypeError):
                pass

        status_filter = request.query_params.get("status")
        if status_filter:
            events = [e for e in events if e.status == status_filter]

        search = request.query_params.get("search")
        if search:
            events = [e for e in events if search.lower() in e.event_name.lower()]

        ordering = request.query_params.get("ordering", "start_time")
        reverse = ordering.startswith("-")
        order_field = ordering.lstrip("-")
        if events and hasattr(events[0], order_field):

            def sort_key(x):
                val = getattr(x, order_field)
                if val is None:
                    return datetime.min
                return val

            events = sorted(events, key=sort_key, reverse=reverse)

        return get_paginated_response(self.get_serializer_class(), events, request)

    def retrieve(self, request, pk=None):
        try:
            event_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid event ID"}, status=status.HTTP_400_BAD_REQUEST)

        event = self.service.get_event_by_id(event_id)
        if not event:
            return Response({"detail": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(event)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            event = self.service.create_event(serializer.validated_data)
            response_serializer = EventSerializer(event)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except self.service.EventServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            event_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid event ID"}, status=status.HTTP_400_BAD_REQUEST)

        event = self.service.get_event_by_id(event_id)
        if not event:
            return Response({"detail": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        # Use Django ORM object for permission check (has tournament relation)
        try:
            django_event = DjangoEvent.objects.get(pk=event_id)
            self.check_object_permissions(request, django_event)
        except DjangoEvent.DoesNotExist:
            return Response({"detail": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = EventSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            event = self.service.update_event(event_id, serializer.validated_data)
            response_serializer = EventSerializer(event)
            return Response(response_serializer.data)
        except self.service.EventServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        try:
            event_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid event ID"}, status=status.HTTP_400_BAD_REQUEST)

        event = self.service.get_event_by_id(event_id)
        if not event:
            return Response({"detail": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        # Use Django ORM object for permission check (has tournament relation)
        try:
            django_event = DjangoEvent.objects.get(pk=event_id)
            self.check_object_permissions(request, django_event)
        except DjangoEvent.DoesNotExist:
            return Response({"detail": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            success = self.service.delete_event(event_id)
            if not success:
                return Response({"detail": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except self.service.EventServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["put"], url_path="live-ranking")
    def update_live_ranking(self, request, pk=None):
        try:
            event_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid event ID"}, status=status.HTTP_400_BAD_REQUEST)

        live_ranking = request.data.get("live_ranking")
        if live_ranking is None:
            return Response({"detail": "live_ranking parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = self.service.update_event(event_id, {"live_ranking": live_ranking})
            serializer = EventSerializer(event)
            return Response(serializer.data)
        except self.service.EventServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], url_path="participants")
    def get_participants(self, request, pk=None):
        try:
            event_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid event ID"}, status=status.HTTP_400_BAD_REQUEST)

        from backend.apps.fencing_organizer.modules.event_participant.serializers import EventParticipantSerializer

        django_participants = DjangoEventParticipant.objects.filter(event_id=event_id).select_related("fencer")
        serializer = EventParticipantSerializer(django_participants, many=True)

        return Response({"event_id": pk, "participant_count": django_participants.count(), "participants": serializer.data})

    @action(detail=True, methods=["put"], url_path="participants/sync")
    def sync_participants(self, request, pk=None):
        try:
            event_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid event ID"}, status=status.HTTP_400_BAD_REQUEST)

        fencer_ids = request.data.get("fencer_ids")
        if not isinstance(fencer_ids, list):
            return Response({"detail": "fencer_ids must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                DjangoEventParticipant.objects.filter(event_id=event_id).delete()

                valid_fencers = DjangoFencer.objects.filter(id__in=fencer_ids)
                valid_fencer_ids = [f.id for f in valid_fencers]

                new_participants = [DjangoEventParticipant(event_id=event_id, fencer_id=f_id) for f_id in valid_fencer_ids]
                DjangoEventParticipant.objects.bulk_create(new_participants)

            return Response({"message": f"Successfully synced {len(valid_fencer_ids)} participants", "synced_count": len(valid_fencer_ids)})
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post", "get"], url_path="stages/(?P<stage_id>[^/.]+)/pools")
    def stage_pools(self, request, pk=None, stage_id=None):
        try:
            event_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid event ID"}, status=status.HTTP_400_BAD_REQUEST)

        if request.method == "GET":
            pools = DjangoPool.objects.filter(event_id=event_id, stage_id=stage_id).order_by("pool_number")
            from backend.apps.fencing_organizer.modules.pool.serializers import PoolSerializer

            return Response(PoolSerializer(pools, many=True).data)

        elif request.method == "POST":
            pools_data = request.data
            if not isinstance(pools_data, list):
                return Response({"detail": "Expected a list of pools"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                with transaction.atomic():
                    DjangoPool.objects.filter(event_id=event_id, stage_id=stage_id).delete()

                    new_pools = []
                    for p_data in pools_data:
                        new_pools.append(
                            DjangoPool(
                                event_id=event_id,
                                stage_id=stage_id,
                                pool_number=p_data.get("pool_number"),
                                fencer_ids=p_data.get("fencer_ids", []),
                            )
                        )

                    DjangoPool.objects.bulk_create(new_pools)

                return Response(
                    {"message": f"Successfully saved {len(new_pools)} pools to stage {stage_id}"}, status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["put", "get"], url_path="stages/(?P<stage_id>[^/.]+)/detree")
    def stage_detree(self, request, pk=None, stage_id=None):
        try:
            event_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid event ID"}, status=status.HTTP_400_BAD_REQUEST)

        event = self.service.get_event_by_id(event_id)
        if not event:
            return Response({"detail": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == "GET":
            tree_data = event.de_trees.get(stage_id) if event.de_trees else None
            return Response(tree_data if tree_data else [])

        elif request.method == "PUT":
            tree_data = request.data.get("tree_data")
            if tree_data is None:
                if isinstance(request.data, list):
                    tree_data = request.data
                else:
                    return Response({"detail": "tree_data is required"}, status=status.HTTP_400_BAD_REQUEST)

            current_trees = dict(event.de_trees) if event.de_trees else {}
            current_trees[stage_id] = tree_data

            try:
                self.service.update_event(event_id, {"de_trees": current_trees})
                return Response({"message": "Saved successfully"})
            except self.service.EventServiceError as e:
                return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="by_tournament")
    def by_tournament(self, request):
        tournament_id = request.query_params.get("tournament_id")
        if not tournament_id:
            return Response({"detail": "tournament_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tournament_uuid = UUID(tournament_id)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid tournament ID"}, status=status.HTTP_400_BAD_REQUEST)

        events = self.service.get_events_by_tournament(tournament_uuid)

        return get_paginated_response(self.get_serializer_class(), events, request)
