from django.urls import path, include
from rest_framework.routers import DefaultRouter

from backend.apps.cluster.views import SyncLogViewSet, SyncStateViewSet

router = DefaultRouter()
router.register(r"sync-logs", SyncLogViewSet, basename="sync-log")
router.register(r"sync-states", SyncStateViewSet, basename="sync-state")

urlpatterns = [
    path("", include(router.urls)),
]
