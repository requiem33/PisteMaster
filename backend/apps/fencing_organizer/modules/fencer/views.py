from uuid import UUID

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
from backend.apps.fencing_organizer.services.fencer_service import FencerService
from backend.apps.fencing_organizer.utils.pagination import get_paginated_response
from .serializers import (
    FencerSerializer,
    FencerCreateSerializer,
    FencerUpdateSerializer,
    FencerSearchSerializer,
)


class FencerViewSet(viewsets.GenericViewSet):
    """
    Fencer API - Clean Architecture Implementation

    All operations go through Service layer.
    Service returns Domain models (dataclasses).
    Serializer handles Domain model serialization via DomainModelSerializer.
    """

    queryset = DjangoFencer.objects.all().order_by("last_name", "first_name")
    serializer_class = FencerSerializer
    service = FencerService()
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["gender", "country_code", "primary_weapon"]
    search_fields = ["first_name", "last_name", "display_name", "fencing_id"]
    ordering_fields = [
        "last_name",
        "first_name",
        "current_ranking",
        "created_at",
        "updated_at",
    ]
    ordering = ["last_name", "first_name"]

    def get_serializer_class(self):
        if self.action == "create":
            return FencerCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return FencerUpdateSerializer
        elif self.action == "search":
            return FencerSearchSerializer
        return FencerSerializer

    def get_permissions(self):
        if self.action in [
            "list",
            "retrieve",
            "search",
            "bulk_save",
            "by_country",
            "by_weapon",
            "stats",
            "top_ranked",
        ]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request):
        fencers = self.service.get_all_fencers()

        country_code = request.query_params.get("country_code")
        if country_code:
            fencers = [f for f in fencers if f.country_code == country_code.upper()]

        gender = request.query_params.get("gender")
        if gender:
            fencers = [f for f in fencers if f.gender == gender.upper()]

        weapon = request.query_params.get("primary_weapon")
        if weapon:
            fencers = [f for f in fencers if f.primary_weapon == weapon.upper()]

        search = request.query_params.get("search")
        if search:
            search_lower = search.lower()
            fencers = [
                f
                for f in fencers
                if search_lower in f.first_name.lower()
                or search_lower in f.last_name.lower()
                or (f.display_name and search_lower in f.display_name.lower())
                or (f.fencing_id and search_lower in f.fencing_id.lower())
            ]

        ordering = request.query_params.get("ordering", "last_name")
        reverse = ordering.startswith("-")
        order_field = ordering.lstrip("-")
        if fencers and hasattr(fencers[0], order_field):
            fencers = sorted(
                fencers, key=lambda x: getattr(x, order_field) or "", reverse=reverse
            )

        return get_paginated_response(self.get_serializer_class(), fencers, request)

    def retrieve(self, request, pk=None):
        try:
            fencer_id = UUID(pk)
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid fencer ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        fencer = self.service.get_fencer_by_id(fencer_id)
        if not fencer:
            return Response(
                {"detail": "Fencer not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(fencer)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            fencer = self.service.create_fencer(serializer.validated_data)
            response_serializer = FencerSerializer(fencer)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except self.service.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def update(self, request, pk=None):
        try:
            fencer_id = UUID(pk)
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid fencer ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            fencer = self.service.update_fencer(fencer_id, serializer.validated_data)
            response_serializer = FencerSerializer(fencer)
            return Response(response_serializer.data)
        except self.service.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def partial_update(self, request, pk=None):
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        try:
            fencer_id = UUID(pk)
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid fencer ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            success = self.service.delete_fencer(fencer_id)
            if success:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {"detail": "Delete failed"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except self.service.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["post"], url_path="bulk-save")
    def bulk_save(self, request):
        fencers_data = request.data
        if not isinstance(fencers_data, list):
            return Response(
                {"detail": "Expected a list of fencers"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        saved_fencers = []
        errors = []

        for fencer_data in fencers_data:
            try:
                fencer_id = fencer_data.get("id")
                if fencer_id:
                    try:
                        fencer_uuid = UUID(fencer_id)
                        existing = self.service.get_fencer_by_id(fencer_uuid)
                        if existing:
                            fencer = self.service.update_fencer(
                                existing.id, fencer_data
                            )
                        else:
                            fencer = self.service.create_fencer(fencer_data)
                    except (ValueError, TypeError):
                        fencer = self.service.create_fencer(fencer_data)
                else:
                    fencer = self.service.create_fencer(fencer_data)

                saved_fencers.append(fencer)
            except Exception as e:
                errors.append({"data": fencer_data, "error": str(e)})

        return Response(
            {
                "saved_count": len(saved_fencers),
                "error_count": len(errors),
                "errors": errors,
                "results": [FencerSerializer(f).data for f in saved_fencers],
            }
        )

    @action(detail=False, methods=["post"], url_path="search")
    def search(self, request):
        serializer = FencerSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data["query"]
        limit = serializer.validated_data.get("limit", 50)

        try:
            fencers = self.service.search_fencers(query, limit)
            return Response(
                {
                    "query": query,
                    "count": len(fencers),
                    "results": [FencerSerializer(f).data for f in fencers],
                }
            )
        except self.service.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False, methods=["get"], url_path="by-country/(?P<country_code>[^/.]+)"
    )
    def by_country(self, request, country_code=None):
        try:
            fencers = self.service.get_fencers_by_country(country_code.upper())
            return Response(
                {
                    "country_code": country_code.upper(),
                    "count": len(fencers),
                    "results": [FencerSerializer(f).data for f in fencers],
                }
            )
        except self.service.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], url_path="by-weapon/(?P<weapon>[^/.]+)")
    def by_weapon(self, request, weapon=None):
        try:
            fencers = self.service.get_fencers_by_weapon(weapon.upper())
            return Response(
                {
                    "weapon": weapon.upper(),
                    "count": len(fencers),
                    "results": [FencerSerializer(f).data for f in fencers],
                }
            )
        except self.service.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        try:
            statistics = self.service.get_statistics()
            return Response(statistics)
        except self.service.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], url_path="top-ranked")
    def top_ranked(self, request):
        limit = int(request.query_params.get("limit", 100))
        country = request.query_params.get("country")

        try:
            fencers = self.service.get_top_ranked_fencers(limit, country)
            return Response(
                {
                    "limit": limit,
                    "country": country,
                    "count": len(fencers),
                    "results": [FencerSerializer(f).data for f in fencers],
                }
            )
        except self.service.FencerServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
