from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventParticipantViewSet

router = DefaultRouter()
router.register(r'', EventParticipantViewSet, basename='event_participant')

urlpatterns = [
    path('', include(router.urls)),
]
