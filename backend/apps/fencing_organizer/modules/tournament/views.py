from datetime import date

from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets
from uuid import UUID

from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament
from backend.apps.fencing_organizer.services.tournament_service import TournamentService
from backend.apps.fencing_organizer.utils.pagination import get_paginated_response
from .serializers import TournamentSerializer, TournamentCreateSerializer


class TournamentViewSet(viewsets.GenericViewSet):
    """
    Tournament API - Clean Architecture Implementation

    All operations go through Service layer.
    Service returns Domain models (dataclasses).
    Serializer handles Domain model serialization via DomainModelSerializer.

    list: Get tournament list
    retrieve: Get single tournament
    create: Create tournament
    update: Update tournament
    partial_update: Partial update tournament
    destroy: Delete tournament
    upcoming: Get upcoming tournaments
    ongoing: Get ongoing tournaments
    statistics: Get tournament statistics
    """

    queryset = DjangoTournament.objects.all()
    serializer_class = TournamentSerializer
    service = TournamentService()
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "start_date", "end_date"]
    search_fields = ["tournament_name", "organizer", "location"]
    ordering_fields = ["tournament_name", "start_date", "end_date", "created_at"]
    ordering = ["-start_date"]

    def get_permissions(self):
        if self.action in [
            "create",
            "list",
            "retrieve",
            "update",
            "partial_update",
            "destroy",
        ]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return TournamentCreateSerializer
        return TournamentSerializer

    def list(self, request):
        tournaments = self.service.get_all_tournaments()

        search = request.query_params.get("search")
        if search:
            tournaments = [
                t
                for t in tournaments
                if search.lower() in t.tournament_name.lower()
                or (t.organizer and search.lower() in t.organizer.lower())
                or (t.location and search.lower() in t.location.lower())
            ]

        status_filter = request.query_params.get("status")
        if status_filter:
            tournaments = [t for t in tournaments if t.status == status_filter]

        ordering = request.query_params.get("ordering", "-start_date")
        reverse = ordering.startswith("-")
        order_field = ordering.lstrip("-")
        if hasattr(tournaments[0] if tournaments else None, order_field):
            tournaments = sorted(
                tournaments, key=lambda x: getattr(x, order_field), reverse=reverse
            )

        return get_paginated_response(self.get_serializer_class(), tournaments, request)

    def retrieve(self, request, pk=None):
        try:
            tournament_id = UUID(pk)
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid tournament ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        tournament = self.service.get_tournament_by_id(tournament_id)
        if not tournament:
            return Response(
                {"detail": "Tournament not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(tournament)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            tournament = self.service.create_tournament(serializer.validated_data)
            response_serializer = self.get_serializer(tournament)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except self.service.TournamentServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def update(self, request, pk=None):
        try:
            tournament_id = UUID(pk)
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid tournament ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            tournament = self.service.update_tournament(
                tournament_id, serializer.validated_data
            )
            response_serializer = self.get_serializer(tournament)
            return Response(response_serializer.data)
        except self.service.TournamentServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def partial_update(self, request, pk=None):
        try:
            tournament_id = UUID(pk)
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid tournament ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TournamentSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            tournament = self.service.update_tournament(
                tournament_id, serializer.validated_data
            )
            response_serializer = TournamentSerializer(tournament)
            return Response(response_serializer.data)
        except self.service.TournamentServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def destroy(self, request, pk=None):
        try:
            tournament_id = UUID(pk)
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid tournament ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            success = self.service.delete_tournament(tournament_id)
            if not success:
                return Response(
                    {"detail": "Tournament not found"}, status=status.HTTP_404_NOT_FOUND
                )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except self.service.TournamentServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        days = int(request.query_params.get("days", 30))
        tournaments = self.service.get_upcoming_tournaments(days)

        return get_paginated_response(self.get_serializer_class(), tournaments, request)

    @action(detail=False, methods=["get"])
    def ongoing(self, request):
        tournaments = self.service.get_ongoing_tournaments()

        return get_paginated_response(self.get_serializer_class(), tournaments, request)

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        total_tournaments = DjangoTournament.objects.count()
        status_stats = (
            DjangoTournament.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

        today = date.today()
        upcoming_count = DjangoTournament.objects.filter(start_date__gte=today).count()
        ongoing_count = DjangoTournament.objects.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today)
        ).count()
        past_count = DjangoTournament.objects.filter(end_date__lt=today).count()

        return Response(
            {
                "total_tournaments": total_tournaments,
                "upcoming_count": upcoming_count,
                "ongoing_count": ongoing_count,
                "past_count": past_count,
                "status_distribution": list(status_stats),
                "date_range": {"today": today.isoformat(), "upcoming_days": 30},
            }
        )

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        try:
            tournament_id = UUID(pk)
            tournament = self.service.get_tournament_by_id(tournament_id)
            if not tournament:
                return Response(
                    {"detail": "Tournament not found"}, status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {
                    "tournament_id": pk,
                    "current_status": {
                        "code": tournament.status,
                        "since": (
                            tournament.updated_at.isoformat()
                            if tournament.updated_at
                            else None
                        ),
                    },
                    "created_at": (
                        tournament.created_at.isoformat()
                        if tournament.created_at
                        else None
                    ),
                    "last_updated": (
                        tournament.updated_at.isoformat()
                        if tournament.updated_at
                        else None
                    ),
                }
            )
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid tournament ID"}, status=status.HTTP_400_BAD_REQUEST
            )
