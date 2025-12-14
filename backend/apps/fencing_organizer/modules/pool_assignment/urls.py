from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PoolAssignmentViewSet

router = DefaultRouter()
router.register(r'', PoolAssignmentViewSet, basename='pool_assignment')

urlpatterns = [
    path('', include(router.urls)),
]
