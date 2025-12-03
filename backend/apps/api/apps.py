# backend/apps/api/apps.py
from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.api'  # 完整的Python路径
    # 可选但推荐：定义一个更友好的名字
    verbose_name = 'API'
    # 【关键】指定该Django App的核心模型来自哪个模块
    # 这建立了 Django ORM 与 core/ 的关联
    module_path = 'core.models'