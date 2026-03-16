from uuid import UUID

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from backend.apps.fencing_organizer.modules.pool.models import DjangoPool
from backend.apps.fencing_organizer.services.pool_service import PoolService
from backend.apps.fencing_organizer.utils.pagination import get_paginated_response
from .serializers import PoolSerializer, PoolCreateSerializer, PoolUpdateSerializer


class PoolViewSet(viewsets.GenericViewSet):
    """
    Pool API - Clean Architecture Implementation

    All operations go through Service layer.
    Service returns Domain models (dataclasses).
    Serializer handles Domain model serialization via DomainModelSerializer.
    """

    queryset = DjangoPool.objects.all().order_by('event', 'stage_id', 'pool_number')
    serializer_class = PoolSerializer
    service = PoolService()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event', 'stage_id', 'status', 'is_completed']
    search_fields = ['event__event_name']
    ordering_fields = ['pool_number', 'created_at']
    ordering = ['pool_number']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'by_event', 'update_results', 'create', 'update', 'destroy']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return PoolCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PoolUpdateSerializer
        return PoolSerializer

    def list(self, request):
        pools = self.service.get_all_pools()

        event_id = request.query_params.get('event')
        if event_id:
            try:
                event_uuid = UUID(event_id)
                pools = [p for p in pools if p.event_id == event_uuid]
            except (ValueError, TypeError):
                pass

        stage_id = request.query_params.get('stage_id')
        if stage_id:
            pools = [p for p in pools if p.stage_id == stage_id]

        status_filter = request.query_params.get('status')
        if status_filter:
            pools = [p for p in pools if p.status == status_filter]

        ordering = request.query_params.get('ordering', 'pool_number')
        reverse = ordering.startswith('-')
        order_field = ordering.lstrip('-')
        if pools and hasattr(pools[0], order_field):
            pools = sorted(pools, key=lambda x: getattr(x, order_field) or 0, reverse=reverse)

        return get_paginated_response(
            self.get_serializer_class(),
            pools,
            request
        )

    def retrieve(self, request, pk=None):
        try:
            pool_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid pool ID"}, status=status.HTTP_400_BAD_REQUEST)

        pool = self.service.get_pool_by_id(pool_id)
        if not pool:
            return Response({"detail": "Pool not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(pool)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            pool = self.service.create_pool(serializer.validated_data)
            response_serializer = PoolSerializer(pool)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except self.service.PoolServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            pool_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid pool ID"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            pool = self.service.update_pool(pool_id, serializer.validated_data)
            response_serializer = PoolSerializer(pool)
            return Response(response_serializer.data)
        except self.service.PoolServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        try:
            pool_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid pool ID"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            success = self.service.delete_pool(pool_id)
            if not success:
                return Response({"detail": "Pool not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except self.service.PoolServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='results')
    def update_results(self, request, pk=None):
        try:
            pool_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid pool ID"}, status=status.HTTP_400_BAD_REQUEST)

        results = request.data.get('results')
        stats = request.data.get('stats')
        is_locked = request.data.get('is_locked')

        update_data = {}
        if results is not None:
            update_data['results'] = results
        if stats is not None:
            update_data['stats'] = stats
        if is_locked is not None:
            update_data['is_locked'] = is_locked

        try:
            pool = self.service.update_pool(pool_id, update_data)
            response_data = {"message": "Updated successfully"}
            if is_locked is not None:
                response_data["is_locked"] = is_locked
            return Response(response_data)
        except self.service.PoolServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='by-event/(?P<event_id>[^/.]+)')
    def by_event(self, request, event_id=None):
        try:
            event_uuid = UUID(event_id)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid event ID format"}, status=status.HTTP_400_BAD_REQUEST)

        pools = self.service.get_pools_by_event(event_uuid)

        stage_id = request.query_params.get('stage_id')
        if stage_id:
            pools = [p for p in pools if p.stage_id == stage_id]

        serializer = PoolSerializer(pools, many=True)
        return Response(serializer.data)
