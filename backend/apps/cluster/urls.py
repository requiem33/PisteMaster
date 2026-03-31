from django.urls import path, include
from rest_framework.routers import DefaultRouter

from backend.apps.cluster.views import (
    SyncLogViewSet,
    SyncStateViewSet,
    SyncViewSet,
    ClusterStatusViewSet,
)
from backend.apps.cluster.views.sync import sync_ack

router = DefaultRouter()
router.register(r"sync-logs", SyncLogViewSet, basename="sync-log")
router.register(r"sync-states", SyncStateViewSet, basename="sync-state")
router.register(r"sync", SyncViewSet, basename="sync")
router.register(r"status", ClusterStatusViewSet, basename="cluster-status")

urlpatterns = [
    path("", include(router.urls)),
    path("ack", sync_ack, name="sync-ack-standalone"),
]
