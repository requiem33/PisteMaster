# backend/apps/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# 创建路由器并注册视图集
router = DefaultRouter()

urlpatterns = [
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
