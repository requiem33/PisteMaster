from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PoolBoutViewSet

router = DefaultRouter()
router.register(r'', PoolBoutViewSet, basename='pool_bout')

urlpatterns = [
    path('', include(router.urls)),
]
