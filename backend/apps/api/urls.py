# backend/apps/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器并注册视图集
router = DefaultRouter()
router.register(r'fencers', views.FencerViewSet, basename='fencer')

urlpatterns = [
    # API 根路径，会列出所有已注册的API端点
    path('', include(router.urls)),

    # 如果需要，可以在这里添加额外的自定义API视图
    # path('custom-endpoint/', views.custom_view, name='custom'),
]

# 可选：为API登录界面添加认证URL（方便在浏览器中测试）
urlpatterns += [
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]