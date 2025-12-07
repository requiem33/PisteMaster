# backend/apps/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .my_views.match_generation_views import (
    GenerateMatchesAPI,
    ClearMatchesAPI,
    RegenerateMatchesAPI
)

# 创建路由器并注册视图集
router = DefaultRouter()
router.register(r'fencers', views.FencerViewSet, basename='fencer')
router.register(r'competition-items', views.CompetitionItemViewSet, basename='competition-item')
router.register(r'matches', views.MatchViewSet, basename='match')

urlpatterns = [
    # API 根路径
    path('', include(router.urls)),

    # 比赛生成相关API
    path(
        'competition-items/<int:item_id>/generate-matches/',
        GenerateMatchesAPI.as_view(),
        name='generate-matches'
    ),
    path(
        'competition-items/<int:item_id>/clear-matches/',
        ClearMatchesAPI.as_view(),
        name='clear-matches'
    ),
    path(
        'competition-items/<int:item_id>/regenerate-matches/',
        RegenerateMatchesAPI.as_view(),
        name='regenerate-matches'
    ),

    # 认证
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]