from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.api'  # 完整的Python路径
    # 可选但推荐：定义一个更友好的名字
    verbose_name = 'API'
