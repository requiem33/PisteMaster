# AGENTS.md - PisteMaster Project Guide

This document provides essential information for AI coding agents working in this repository.

## Project Overview

PisteMaster is a full-stack fencing tournament management system with:
- **Backend**: Django 4.2 + Django REST Framework (Python)
- **Frontend**: Vue 3 + TypeScript + Vite + Element Plus
- **Core**: Shared Python domain models, interfaces, and services
- **Desktop App**: PySide6 (Qt for Python) - early development

---

## Build/Lint/Test Commands

### Python (Backend & Core)

```bash
# Run all tests (from project root)
pytest

# Run tests in specific directory
pytest tests/
pytest backend/apps/fencing_organizer/tests/

# Run single test file
pytest tests/unit/test_models/test_tournament.py

# Run single test class
pytest tests/unit/test_models/test_tournament.py::TestTournament

# Run single test method
pytest tests/unit/test_models/test_tournament.py::TestTournament::test_create_valid_tournament

# Run with verbose output
pytest -v tests/unit/test_models/test_tournament.py

# Run Django tests
cd backend && python manage.py test

# Lint with flake8
flake8 backend/ core/ tests/ --exclude=venv,migrations,__pycache__

# Format with black
black backend/ core/ tests/ --exclude="venv|migrations"

# Start Django development server
cd backend && python manage.py runserver
```

### Frontend (web_frontend)

```bash
# Navigate to frontend directory first
cd web_frontend

# Install dependencies
npm install

# Start development server (runs on port 3001)
npm run dev

# Build for production (includes type checking)
npm run build

# Run linter (ESLint)
npm run lint

# Format code (Prettier)
npm run format

# Run tests (Vitest)
npm run test

# Run single test file
npx vitest run path/to/test.spec.ts

# Run tests matching a pattern
npx vitest run -t "test name pattern"

# Run tests with UI
npx vitest --ui
```

### Root-level convenience scripts

```bash
# Run both backend and frontend in development
npm run dev

# Install all dependencies (backend + frontend)
npm run install:all
```

---

## Code Style Guidelines

### Python Style

#### Imports
Order imports in three groups, separated by blank lines:
1. Standard library imports
2. Third-party imports
3. Local/application imports

```python
# Standard library
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

# Third-party
from django.db import transaction
from rest_framework import serializers

# Local imports
from core.models.tournament import Tournament
from backend.apps.fencing_organizer.repositories.tournament_repo import DjangoTournamentRepository
```

#### Type Hints
- Always use type hints for function parameters and return types
- Use `Optional[T]` for nullable types
- Use `List[T]`, `Dict[K, V]` from `typing` module

```python
def get_tournament_by_id(self, tournament_id: UUID) -> Optional[Tournament]:
    ...

def get_all_tournaments(self) -> List[Tournament]:
    ...
```

#### Dataclasses for Domain Models
Use `@dataclass` decorator for domain models in `core/models/`:

```python
@dataclass
class Tournament:
    tournament_name: str = field(metadata={"max_length": 200})
    start_date: date
    id: UUID = field(default_factory=uuid4)
    organizer: Optional[str] = field(default=None)
```

#### Error Handling
- Create custom exception classes within service classes
- Use descriptive error messages (Chinese comments acceptable)

```python
class TournamentService:
    class TournamentServiceError(Exception):
        def __init__(self, message: str, errors: dict = None):
            self.message = message
            self.errors = errors or {}
            super().__init__(self.message)
```

#### Naming Conventions
- **Classes**: PascalCase (e.g., `TournamentService`, `DjangoTournamentRepository`)
- **Functions/Methods**: snake_case (e.g., `get_tournament_by_id`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_NAME_LENGTH`)
- **Private methods**: prefix with underscore (e.g., `_validate_data`)
- **Django models**: Prefix with `Django` (e.g., `DjangoTournament`)

#### Docstrings
Use Chinese or English docstrings consistently within a module:

```python
def get_tournament_by_id(self, tournament_id: UUID) -> Optional[Tournament]:
    """根据ID获取赛事"""
    ...

def create_tournament(self, tournament_data: dict) -> Tournament:
    """
    创建赛事
    :param tournament_data: 经过 Serializer 验证的、干净的数据字典
    """
    ...
```

---

### TypeScript/Vue Style

#### Prettier Configuration
- No semicolons
- Single quotes
- 2-space indentation
- Print width: 100 characters
- Trailing commas: ES5

#### Vue Component Structure
Use `<script setup lang="ts">` with Composition API:

```vue
<template>
  <!-- Template content -->
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'

const router = useRouter()
const loading = ref(false)
const tournaments = ref<Tournament[]>([])

const loadTournaments = async () => {
  loading.value = true
  try {
    const result = await DataManager.getTournamentList()
    tournaments.value = result ?? []
  } catch (error) {
    console.error('Failed to load tournaments:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTournaments()
})
</script>

<style scoped lang="scss">
/* Styles here */
</style>
```

#### Path Aliases
- Use `@/` for imports from `src/`:
```typescript
import AppHeader from '@/components/layout/AppHeader.vue'
import { DataManager } from '@/services/DataManager'
import type { Tournament } from '@/types/tournament'
```

#### TypeScript Types
- Define interfaces in `src/types/` directory
- Use `interface` for object shapes, `type` for unions/aliases

```typescript
export interface Tournament {
  id: string
  tournament_name: string
  status: 'draft' | 'active' | 'completed'
  is_synced: boolean
}
```

#### Naming Conventions
- **Components**: PascalCase files (e.g., `TournamentList.vue`)
- **Composables**: camelCase with `use` prefix (e.g., `useDataManager.ts`)
- **Stores**: camelCase with `Store` suffix (e.g., `tournamentStore.ts`)
- **Types**: PascalCase interfaces (e.g., `Tournament`)

#### Error Handling
Use try-catch with Element Plus messages:

```typescript
try {
  await DataManager.deleteTournament(id)
  ElMessage.success('删除成功')
} catch (error) {
  console.error('操作失败:', error)
  ElMessage.error('操作失败')
}
```

---

## Project Structure

```
PisteMaster/
├── backend/                    # Django backend
│   ├── PisteMaster/           # Django project settings
│   ├── apps/fencing_organizer/ # Main Django app
│   │   ├── modules/           # Sub-modules (models, views, serializers)
│   │   ├── services/          # Business logic services
│   │   ├── repositories/      # Data access layer
│   │   ├── mappers/           # Domain-DTO mappers
│   │   └── tests/             # Backend tests
│   └── requirements.txt
├── core/                       # Shared Python domain logic
│   ├── models/                 # Domain models (dataclasses)
│   ├── interfaces/             # Repository interfaces (ABC)
│   ├── services/               # Domain services
│   └── constants/              # Constants and enums
├── web_frontend/               # Vue 3 frontend
│   ├── src/
│   │   ├── components/         # Vue components
│   │   ├── views/              # Page views
│   │   ├── services/           # API and data services
│   │   ├── stores/             # Pinia stores
│   │   ├── types/              # TypeScript interfaces
│   │   └── locales/            # i18n translations
│   └── package.json
├── desktop_app/                # PySide6 desktop app
├── tests/                      # Integration/unit tests for core
└── docs/                       # Documentation
```

---

## Important Notes

1. **Database**: Development uses SQLite; production should use PostgreSQL
2. **CORS**: Configured for localhost:3001 and localhost:3002
3. **i18n**: Project supports Chinese (zh-CN) and English (en-US)
4. **Offline Support**: Frontend has IndexedDB for offline data storage
5. **API Documentation**: Available via drf-yasg at `/swagger/` endpoint

---

## Testing Conventions

### Python Tests
- Use `pytest` with `pytest-django`
- Place tests in `tests/` directory or alongside modules in `tests/` subdirectory
- Use `@pytest.mark.django_db` for tests requiring database
- Use fixtures for common test data

### Frontend Tests
- Use Vitest with Vue Test Utils
- Test files should be co-located or in a `__tests__` directory
- Use `describe`/`it` (or `test`) blocks for organization
