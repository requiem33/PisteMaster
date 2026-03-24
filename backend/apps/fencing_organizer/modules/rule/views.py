from uuid import UUID

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from backend.apps.fencing_organizer.modules.rule.models import DjangoRule
from backend.apps.fencing_organizer.modules.elimination_type.models import DjangoEliminationType
from backend.apps.fencing_organizer.modules.ranking_type.models import DjangoRankingType
from backend.apps.fencing_organizer.services.rule_service import RuleService
from backend.apps.fencing_organizer.utils.pagination import get_paginated_response
from .serializers import RuleSerializer, RuleCreateSerializer


class RuleViewSet(viewsets.GenericViewSet):
    """
    Rule API - Clean Architecture Implementation

    Returns only preset rules (is_preset=True) for the list endpoint.
    Custom rules are stored per-event, not in the rules table.

    All operations go through Service layer.
    Service returns Domain models (dataclasses).
    Serializer handles Domain model serialization via DomainModelSerializer.
    """

    queryset = DjangoRule.objects.all()
    serializer_class = RuleSerializer
    service = RuleService()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["elimination_type", "final_ranking_type", "pool_size", "is_preset"]
    search_fields = ["rule_name", "description"]
    ordering_fields = ["rule_name", "pool_size", "total_qualified_count", "created_at"]
    ordering = ["rule_name"]

    def get_permissions(self):
        if self.action in ["list", "retrieve", "types"]:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "create":
            return RuleCreateSerializer
        return RuleSerializer

    def list(self, request):
        """
        Get preset rules list.

        Only returns rules where is_preset=True.
        Custom rules are stored per-event, not here.
        """
        rules = self.service.get_preset_rules()

        search = request.query_params.get("search")
        if search:
            search_lower = search.lower()
            rules = [r for r in rules if search_lower in r.rule_name.lower() or (r.description and search_lower in r.description.lower())]

        ordering = request.query_params.get("ordering", "rule_name")
        reverse = ordering.startswith("-")
        order_field = ordering.lstrip("-")
        if rules and hasattr(rules[0], order_field):
            rules = sorted(rules, key=lambda x: getattr(x, order_field) or "", reverse=reverse)

        return get_paginated_response(self.get_serializer_class(), rules, request)

    def retrieve(self, request, pk=None):
        try:
            rule_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid rule ID"}, status=status.HTTP_400_BAD_REQUEST)

        rule = self.service.get_rule_by_id(rule_id)
        if not rule:
            return Response({"detail": "Rule not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(rule)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            rule = self.service.create_rule(serializer.validated_data)
            response_serializer = RuleSerializer(rule)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except self.service.RuleServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            rule_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid rule ID"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            rule = self.service.update_rule(rule_id, serializer.validated_data)
            response_serializer = RuleSerializer(rule)
            return Response(response_serializer.data)
        except self.service.RuleServiceError as e:
            return Response({"detail": e.message, "errors": e.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            rule_id = UUID(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid rule ID"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            success = self.service.delete_rule(rule_id)
            if not success:
                return Response({"detail": "Rule not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except self.service.RuleServiceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def types(self, request):
        """Get all elimination types and ranking types."""
        elimination_types = DjangoEliminationType.objects.all()
        ranking_types = DjangoRankingType.objects.all()

        return Response(
            {
                "elimination_types": [
                    {"id": str(t.id), "type_code": t.type_code, "display_name": t.display_name} for t in elimination_types
                ],
                "ranking_types": [{"id": str(t.id), "type_code": t.type_code, "display_name": t.display_name} for t in ranking_types],
            }
        )
