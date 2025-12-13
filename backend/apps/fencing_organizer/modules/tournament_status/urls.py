from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TournamentStatusViewSet

router = DefaultRouter()
router.register(r'', TournamentStatusViewSet, basename='tournament-status')

urlpatterns = [
    path('', include(router.urls)),
]
