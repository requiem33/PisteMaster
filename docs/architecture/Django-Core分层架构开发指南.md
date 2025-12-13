# Django分层架构开发指南

## 设计原则

### 1. 架构分层原则

#### 1.1 六边形架构/整洁架构

```
┌─────────────────────────────────────────────────────────────┐
│                       Core (领域层)                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                Domain Entities                      │    │
│  │                + Business Rules                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (框架层)                         │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Service │  │   API   │  │  Repo   │  │ Mappers │        │
│  │ (业务)  │  │  (接口)  │  │ (数据)  │  │  (转换)  │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Framework (技术实现)                       │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │ Django  │  │   ORM   │  │  Admin  │  │   DB    │         │
│  │  REST   │  │ Models  │  │   UI    │  │ Schema  │         │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 1.2 依赖规则

- **向内依赖**：外层可以依赖内层，内层不能依赖外层
- **核心独立**：Core层不依赖任何外部框架
- **接口隔离**：通过接口定义依赖关系

### 2. 各层职责

#### 2.1 Core层（领域层）

- **位置**：`/core/`
- **职责**：纯粹的业务模型和接口定义
- **要求**：
    - 无框架依赖
    - 只定义"做什么"，不定义"怎么做"
    - 可独立测试和运行

#### 2.2 Backend层（实现层）

- **位置**：`/backend/apps/{app_name}/`
- **职责**：Django框架的具体实现
- **包含**：Service、Repository、Mapper、API等实现

### 3. 开发规范

#### 3.1 命名规范

```
# Core层
Fencer                    # 领域实体类
FencerRepositoryInterface # 仓库接口

# Backend层
DjangoFencer              # ORM模型类
FencerService             # 业务服务类
FencerMapper              # 对象映射器
FencerSerializer          # API序列化器
FencerViewSet             # API视图集
```

#### 3.2 文件结构规范

```
{app_name}/
├── __init__.py
├── apps.py              # Django应用配置
├── admin.py             # 应用级Admin配置
├── urls.py              # 应用级路由
├── modules/             # 功能模块
│   └── {module_name}/
│       ├── __init__.py
│       ├── models.py    # ORM模型
│       ├── admin.py     # 模块Admin
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
├── mappers/             # 对象映射
│   └── {module_name}_mapper.py
├── repositories/        # 数据访问
│   └── {module_name}_repo.py
└── services/            # 业务逻辑
    └── {module_name}_service.py
```

## 开发流程

### 阶段一：Core层开发

#### 步骤1.1 创建领域实体

```python
# core/models/{module_name}.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class Fencer:
    """击剑运动员领域实体"""
    id: UUID
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    gender: Optional[str] = None
    country_code: Optional[str] = None
    birth_date: Optional[datetime] = None
    fencing_id: Optional[str] = None
    current_ranking: Optional[int] = None
    primary_weapon: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """计算全名"""
        return f"{self.last_name} {self.first_name}"
```

#### 步骤1.2 定义仓库接口

```python
# core/interfaces/{module_name}_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from core.models.fencer import Fencer


class FencerRepositoryInterface(ABC):
    """Fencer仓库接口"""

    @abstractmethod
    def get_fencer_by_id(self, fencer_id: UUID) -> Optional[Fencer]:
        pass

    @abstractmethod
    def save_fencer(self, fencer: Fencer) -> Fencer:
        pass

    @abstractmethod
    def get_fencers_by_country(self, country_code: str) -> List[Fencer]:
        pass
```

### 阶段二：Django集成开发

#### 步骤2.1 创建Django应用

```bash
# 在backend目录下创建Django应用
python manage.py startapp fencing_organizer

# 创建标准目录结构
mkdir -p backend/apps/fencing_organizer/{modules,mappers,repositories,services}
```

#### 步骤2.2 创建ORM模型

```python
# backend/apps/fencing_organizer/modules/fencer/models.py
from django.db import models
from uuid import uuid4


class DjangoFencer(models.Model):
    """Fencer的Django ORM模型"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # ... 其他字段

    class Meta:
        db_table = 'fencer'
        indexes = [
            models.Index(fields=['country_code'], name='idx_fencer_country'),
            models.Index(fields=['last_name', 'first_name'], name='idx_fencer_name'),
        ]

    def __str__(self):
        return f"{self.last_name} {self.first_name}"
```

#### 步骤2.3 生成数据库迁移

```bash
# 生成迁移文件
python manage.py makemigrations fencing_organizer

# 查看生成的SQL
python manage.py sqlmigrate fencing_organizer 0001

# 执行迁移
python manage.py migrate
```

### 阶段三：数据转换层开发

#### 步骤3.1 创建Mapper

```python
# backend/apps/fencing_organizer/mappers/fencer_mapper.py
from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
from core.models.fencer import Fencer


class FencerMapper:
    """Fencer对象映射器"""

    @staticmethod
    def to_domain(django_fencer: DjangoFencer) -> Fencer:
        """Django ORM → Core Domain"""
        return Fencer(
            id=django_fencer.id,
            first_name=django_fencer.first_name,
            last_name=django_fencer.last_name,
            # ... 字段映射
        )

    @staticmethod
    def to_orm_data(fencer: Fencer) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": fencer.id,
            "first_name": fencer.first_name,
            "last_name": fencer.last_name,
            # ... 字段映射
        }
```

#### 步骤3.2 实现Repository

```python
# backend/apps/fencing_organizer/repositories/fencer_repo.py
from uuid import UUID
from backend.apps.fencing_organizer.mappers.fencer_mapper import FencerMapper
from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
from core.interfaces.fencer_repository import FencerRepositoryInterface
from core.models.fencer import Fencer


class DjangoFencerRepository(FencerRepositoryInterface):
    """Fencer仓库的Django实现"""

    def get_fencer_by_id(self, fencer_id: UUID) -> Fencer | None:
        try:
            django_fencer = DjangoFencer.objects.get(pk=fencer_id)
            return FencerMapper.to_domain(django_fencer)
        except DjangoFencer.DoesNotExist:
            return None

    def save_fencer(self, fencer: Fencer) -> Fencer:
        orm_data = FencerMapper.to_orm_data(fencer)
        django_fencer, created = DjangoFencer.objects.update_or_create(
            id=fencer.id,
            defaults=orm_data
        )
        return FencerMapper.to_domain(django_fencer)
```

### 阶段四：业务逻辑层开发

#### 步骤4.1 创建Service

```python
# backend/apps/fencing_organizer/services/fencer_service.py
from typing import List, Optional
from uuid import UUID
from core.models.fencer import Fencer
from backend.apps.fencing_organizer.repositories.fencer_repo import DjangoFencerRepository


class FencerService:
    """Fencer业务服务"""

    def __init__(self, repository: Optional[DjangoFencerRepository] = None):
        self.repository = repository or DjangoFencerRepository()

    def create_fencer(self, fencer_data: dict) -> Fencer:
        """创建运动员"""
        # 1. 业务规则验证
        self._validate_fencer_data(fencer_data)

        # 2. 创建Domain对象
        fencer = Fencer(**fencer_data)

        # 3. 自动生成display_name
        if not fencer.display_name:
            fencer.display_name = f"{fencer.first_name} {fencer.last_name}"

        # 4. 通过Repository保存
        return self.repository.save_fencer(fencer)

    def _validate_fencer_data(self, data: dict) -> None:
        """业务规则验证"""
        errors = {}
        if not data.get('first_name'):
            errors['first_name'] = "名不能为空"
        if not data.get('last_name'):
            errors['last_name'] = "姓不能为空"
        if errors:
            raise ValueError(f"数据验证失败: {errors}")
```

### 阶段五：API层开发

#### 步骤5.1 创建Serializer

```python
# backend/apps/fencing_organizer/modules/fencer/serializers.py
from rest_framework import serializers
from .models import DjangoFencer


class FencerSerializer(serializers.ModelSerializer):
    """Fencer API序列化器"""

    class Meta:
        model = DjangoFencer
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """数据验证"""
        if not data.get('first_name') or not data.get('last_name'):
            raise serializers.ValidationError("姓和名是必填字段")

        # 自动生成display_name
        if not data.get('display_name'):
            data['display_name'] = f"{data['first_name']} {data['last_name']}"

        return data
```

#### 步骤5.2 创建View

```python
# backend/apps/fencing_organizer/modules/fencer/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import DjangoFencer
from .serializers import FencerSerializer
from ..services.fencer_service import FencerService


class FencerViewSet(viewsets.ViewSet):
    """Fencer API视图"""
    serializer_class = FencerSerializer
    service = FencerService()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['country_code', 'gender']
    search_fields = ['first_name', 'last_name']

    def list(self, request):
        """获取列表"""
        queryset = DjangoFencer.objects.all()

        # 应用过滤
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """创建Fencer"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            fencer = self.service.create_fencer(serializer.validated_data)
            django_fencer = DjangoFencer.objects.get(id=fencer.id)
            response_serializer = self.serializer_class(django_fencer)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
```

#### 步骤5.3 配置路由

```python
# backend/apps/fencing_organizer/modules/fencer/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FencerViewSet

router = DefaultRouter()
router.register(r'', FencerViewSet, basename='fencer')

urlpatterns = [
    path('', include(router.urls)),
]

# backend/apps/fencing_organizer/urls.py
from django.urls import path, include

urlpatterns = [
    path('fencers/', include('backend.apps.fencing_organizer.modules.fencer.urls')),
]

# backend/urls.py (项目根路由)
from django.urls import path, include

urlpatterns = [
    path('api/', include('backend.apps.fencing_organizer.urls')),
]
```

### 阶段六：Admin后台开发

#### 步骤6.1 配置Admin

```python
# backend/apps/fencing_organizer/modules/fencer/admin.py
from django.contrib import admin
from .models import DjangoFencer


@admin.register(DjangoFencer)
class FencerAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'country_code', 'fencing_id')
    search_fields = ('first_name', 'last_name', 'fencing_id')
    list_filter = ('country_code', 'gender', 'primary_weapon')
    ordering = ('last_name', 'first_name')
```

#### 步骤6.2 注册Admin

```python
# backend/apps/fencing_organizer/admin.py
from django.contrib import admin
from .modules.fencer.admin import FencerAdmin
# 导入其他模块的Admin配置
```

### 阶段七：配置集成

#### 步骤7.1 配置Django应用

```python
# backend/apps/fencing_organizer/apps.py
from django.apps import AppConfig


class FencingOrganizerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.fencing_organizer'

    def ready(self):
        """应用启动时执行"""
        import backend.apps.fencing_organizer.signals  # 可选：信号处理
```

#### 步骤7.2 添加到INSTALLED_APPS

```python
# backend/settings.py
INSTALLED_APPS = [
    # Django内置应用
    'django.contrib.admin',
    'django.contrib.auth',
    # ...

    # 第三方应用
    'rest_framework',
    'django_filters',

    # 自定义应用
    'backend.apps.fencing_organizer',
]

# REST Framework配置
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

## 测试策略

### 1. Core层测试

```python
# tests/core/test_fencer.py
def test_fencer_full_name():
    """测试领域实体计算属性"""
    fencer = Fencer(
        id=uuid4(),
        first_name="John",
        last_name="Doe"
    )
    assert fencer.full_name == "Doe John"
```

### 2. Service层测试

```python
# tests/backend/services/test_fencer_service.py
def test_create_fencer_service():
    """测试Service业务逻辑"""
    service = FencerService()
    fencer_data = {
        "first_name": "John",
        "last_name": "Doe",
        "country_code": "USA"
    }

    # 测试业务规则
    with pytest.raises(ValueError, match="名不能为空"):
        service.create_fencer({"last_name": "Doe"})
```

### 3. API层测试

```python
# tests/backend/api/test_fencer_api.py
def test_create_fencer_api(client):
    """测试API端点"""
    response = client.post('/api/fencers/', {
        "first_name": "John",
        "last_name": "Doe"
    })
    assert response.status_code == 201
    assert response.data['display_name'] == "John Doe"
```

## 最佳实践

### 1. 代码组织

- 每个Core模型对应一个完整的模块结构
- 保持层间依赖清晰
- 使用接口定义依赖关系

### 2. 错误处理

```python
# 统一异常处理
class DomainError(Exception):
    """领域层异常基类"""
    pass


class ValidationError(DomainError):
    """验证异常"""
    pass


class NotFoundError(DomainError):
    """未找到异常"""
    pass
```

### 3. 性能优化

- Repository层实现复杂查询
- Mapper层缓存转换结果
- Service层实现业务缓存

### 4. 文档生成

```python
# 添加API文档注释
class FencerViewSet(viewsets.ViewSet):
    """
    Fencer资源API
    
    list:
    获取运动员列表
    
    create:
    创建新运动员
    """
```

## 快速检查清单

完成一个Core模型的Django集成后，检查以下项目：

- [ ] Core领域实体定义完成
- [ ] 仓库接口定义完成
- [ ] ORM模型创建完成
- [ ] 数据库迁移生成并执行
- [ ] Mapper双向转换实现
- [ ] Repository接口实现
- [ ] Service业务逻辑实现
- [ ] Serializer验证逻辑完成
- [ ] API视图实现完成
- [ ] URL路由配置完成
- [ ] Admin后台配置完成
- [ ] Django应用注册完成
- [ ] 测试用例编写完成
- [ ] 文档注释补充完成

## 故障排除

### 常见问题1：循环导入

```
# 错误：A导入B，B又导入A
# 解决方案：使用局部导入或在__init__.py中管理导入
```

### 常见问题2：序列化器验证失败

```
# 检查Serializer的validate方法
# 确保to_internal_value正确处理空值
```

### 常见问题3：Mapper转换错误

```
# 检查字段类型匹配
# 确保时区正确处理
```

---
