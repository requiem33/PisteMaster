from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FencerViewSet

router = DefaultRouter()
router.register(r'', FencerViewSet, basename='fencer')

urlpatterns = [
    path('', include(router.urls)),
]
