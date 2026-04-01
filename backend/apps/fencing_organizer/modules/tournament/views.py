from datetime import date

from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import viewsets
from uuid import UUID

from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament
from backend.apps.fencing_organizer.permissions import IsSchedulerOrAdmin, IsTournamentEditor, IsTournamentCreatorOrAdmin
from backend.apps.fencing_organizer.services.tournament_service import TournamentService
from backend.apps.fencing_organizer.utils.pagination import get_paginated_response
from backend.apps.users.models import User
from .serializers import TournamentSerializer, TournamentCreateSerializer, TournamentSchedulerSerializer


class TournamentViewSet(viewsets.GenericViewSet):
    """
    Tournament API - Clean Architecture Implementation

    All operations go through Service layer.
    Service returns Domain models (dataclasses).
    Serializer handles Domain model serialization via DomainModelSerializer.

    list: Get tournament list (public)
    retrieve: Get single tournament (public)
    create: Create tournament (scheduler or admin only)
    update: Update tournament (editor only - admin, creator, or scheduler)
    partial_update: Partial update tournament (editor only)
    destroy: Delete tournament (editor only)
    upcoming: Get upcoming tournaments (public)
    ongoing: Get ongoing tournaments (public)
    statistics: Get tournament statistics (public)
    timeline: Get tournament timeline (public)
    add_scheduler: Add scheduler to tournament (admin or creator only)
    remove_scheduler: Remove scheduler from tournament (admin or creator only)
    """

    queryset = DjangoTournament.objects.all()
    serializer_class = TournamentSerializer
    service = TournamentService()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "start_date", "end_date"]
    search_fields = ["tournament_name", "organizer", "location"]
    ordering_fields = ["tournament_name", "start_date", "end_date", "created_at"]
    ordering = ["-start_date"]

    def get_permissions(self):
        if self.action in ["create"]:
            return [IsSchedulerOrAdmin()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsTournamentEditor()]
        elif self.action in ["add_scheduler", "remove_scheduler"]:
            return [IsTournamentCreatorOrAdmin()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action == "create":
            return TournamentCreateSerializer
        elif self.action in ["add_scheduler", "remove_scheduler"]:
            return TournamentSchedulerSerializer
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
            tournaments = sorted(tournaments, key=lambda x: getattr(x, order_field), reverse=reverse)

        return get_paginated_response(self.get_serializer_class(), tournaments, request)

    def retrieve(self, request, pk=None):
        try:
            tournament_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid tournament ID"}, status=status.HTTP_400_BAD_REQUEST)

        tournament = self.service.get_tournament_by_id(tournament_id)
        if not tournament:
            return Response({"detail": "Tournament not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(tournament)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            validated_data = serializer.validated_data.copy()
            if request.user.is_authenticated:
                validated_data["created_by_id"] = request.user.id

            tournament = self.service.create_tournament(validated_data)
            response_serializer = self.get_serializer(tournament)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except self.service.TournamentServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None, partial=False):
        try:
            tournament_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid tournament ID"}, status=status.HTTP_400_BAD_REQUEST)

        tournament = self.service.get_tournament_by_id(tournament_id)
        if not tournament:
            return Response({"detail": "Tournament not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, tournament)

        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            tournament = self.service.update_tournament(tournament_id, serializer.validated_data)
            response_serializer = self.get_serializer(tournament)
            return Response(response_serializer.data)
        except self.service.TournamentServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        return self.update(request, pk, partial=True)

    def destroy(self, request, pk=None):
        try:
            tournament_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid tournament ID"}, status=status.HTTP_400_BAD_REQUEST)

        tournament = self.service.get_tournament_by_id(tournament_id)
        if not tournament:
            return Response({"detail": "Tournament not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, tournament)

        try:
            success = self.service.delete_tournament(tournament_id)
            if not success:
                return Response({"detail": "Tournament not found"}, status=status.HTTP_404_NOT_FOUND)
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
        status_stats = DjangoTournament.objects.values("status").annotate(count=Count("id")).order_by("status")

        today = date.today()
        upcoming_count = DjangoTournament.objects.filter(start_date__gte=today).count()
        ongoing_count = DjangoTournament.objects.filter(Q(start_date__lte=today) & Q(end_date__gte=today)).count()
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
                return Response({"detail": "Tournament not found"}, status=status.HTTP_404_NOT_FOUND)

            return Response(
                {
                    "tournament_id": pk,
                    "current_status": {
                        "code": tournament.status,
                        "since": tournament.updated_at.isoformat() if tournament.updated_at else None,
                    },
                    "created_at": tournament.created_at.isoformat() if tournament.created_at else None,
                    "last_updated": tournament.updated_at.isoformat() if tournament.updated_at else None,
                }
            )
        except (ValueError, TypeError):
            return Response({"detail": "Invalid tournament ID"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def add_scheduler(self, request, pk=None):
        try:
            tournament_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid tournament ID"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data["user_id"]

        try:
            tournament = DjangoTournament.objects.get(pk=tournament_id)
        except DjangoTournament.DoesNotExist:
            return Response({"detail": "Tournament not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, tournament)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if user.role not in ("ADMIN", "SCHEDULER"):
            return Response({"detail": "Only admins and schedulers can be assigned"}, status=status.HTTP_400_BAD_REQUEST)

        tournament.schedulers.add(user)
        return Response({"success": True, "message": f"User {user.username} added to schedulers"})

    @action(detail=True, methods=["post"])
    def remove_scheduler(self, request, pk=None):
        try:
            tournament_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid tournament ID"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data["user_id"]

        try:
            tournament = DjangoTournament.objects.get(pk=tournament_id)
        except DjangoTournament.DoesNotExist:
            return Response({"detail": "Tournament not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, tournament)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_REQUEST)

        tournament.schedulers.remove(user)
        return Response({"success": True, "message": f"User {user.username} removed from schedulers"})
