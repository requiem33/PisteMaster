from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    message = "Admin permission required."

    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, "role") and request.user.role == "ADMIN"


class IsSchedulerOrAdmin(permissions.BasePermission):
    message = "Scheduler or Admin permission required."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, "role"):
            return False
        return request.user.role in ("ADMIN", "SCHEDULER")


class IsTournamentEditor(permissions.BasePermission):
    message = "You do not have permission to edit this tournament."

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user.is_authenticated:
            return False

        if not hasattr(request.user, "role"):
            return False

        if request.user.role == "ADMIN":
            return True

        # Check if user is the creator (domain model uses created_by_id)
        if hasattr(obj, "created_by_id") and obj.created_by_id:
            if obj.created_by_id == request.user.id:
                return True

        # Check if user is in schedulers (domain model uses scheduler_ids)
        if hasattr(obj, "scheduler_ids") and obj.scheduler_ids:
            if request.user.id in obj.scheduler_ids:
                return True

        return False


class IsTournamentCreatorOrAdmin(permissions.BasePermission):
    message = "Only Admin or Tournament Creator can manage schedulers."

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if not hasattr(request.user, "role"):
            return False

        if request.user.role == "ADMIN":
            return True

        # Check if user is the creator (domain model uses created_by_id)
        if hasattr(obj, "created_by_id") and obj.created_by_id:
            if obj.created_by_id == request.user.id:
                return True

        return False


class IsEventEditor(permissions.BasePermission):
    """
    Permission for event operations.
    - Create: User must be editor of the tournament (tournament_id in request data)
    - Update/Destroy: User must be editor of the event's tournament
    """

    message = "You do not have permission to edit events for this tournament."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # For create action, check tournament_id from request data
        if view.action == "create":
            tournament_id = request.data.get("tournament_id")
            if not tournament_id:
                return False

            return self._check_tournament_editor(request.user, tournament_id)

        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user.is_authenticated:
            return False

        # Get tournament from event
        tournament_id = None
        if hasattr(obj, "tournament_id"):
            tournament_id = obj.tournament_id
        elif hasattr(obj, "tournament"):
            tournament_id = obj.tournament.id

        if not tournament_id:
            return False

        return self._check_tournament_editor(request.user, tournament_id)

    def _check_tournament_editor(self, user, tournament_id):
        """Check if user is an editor of the tournament."""
        from uuid import UUID
        from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament

        try:
            if isinstance(tournament_id, str):
                tournament_id = UUID(tournament_id)
        except (ValueError, TypeError):
            return False

        if not hasattr(user, "role"):
            return False

        # Admins can edit any tournament's events
        if user.role == "ADMIN":
            return True

        try:
            tournament = DjangoTournament.objects.get(id=tournament_id)
        except DjangoTournament.DoesNotExist:
            return False

        # Check if user is tournament creator
        if tournament.created_by_id and tournament.created_by_id == user.id:
            return True

        # Check if user is in tournament schedulers
        if user in tournament.schedulers.all():
            return True

        return False
