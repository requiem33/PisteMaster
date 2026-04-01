# PisteMaster Testing Guide

## Table of Contents

1. [Overview](#overview)
2. [Testing Philosophy](#testing-philosophy)
3. [Test Architecture](#test-architecture)
4. [Test Categories](#test-categories)
5. [Infrastructure Setup](#infrastructure-setup)
6. [Writing Tests](#writing-tests)
7. [Test Utilities](#test-utilities)
8. [Running Tests](#running-tests)
9. [Coverage Requirements](#coverage-requirements)
10. [CI/CD Integration](#cicd-integration)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

---

## Overview

PisteMaster is a full-stack fencing tournament management system with:
- **Backend**: Django 4.2 + Django REST Framework (Python)
- **Frontend**: Vue 3 + TypeScript + Vite + Element Plus
- **Core**: Shared Python domain models, interfaces, and services
- **Desktop App**: Electron + Vue 3 + TypeScript

This document describes the comprehensive testing strategy for all system layers.

### Goals

1. **Ensure Code Quality**: Prevent bugs and regressions
2. **Enable Refactoring**: Safe code changes with confidence
3. **Document Behavior**: Tests as living documentation
4. **Accelerate Development**: Fast feedback loop
5. **Support CI/CD**: Automated quality gates

---

## Testing Philosophy

### Test Pyramid

We follow the test pyramid principle:

```
        ╱╲
       ╱  ╲
      ╱ E2E╲         <- Few, slow, expensive
     ╱──────╲
    ╱Integration╲     <- Some, medium speed
   ╱────────────╲
  ╱   Unit Tests  ╲   <- Many, fast, cheap
 ╱────────────────╲
```

**Priorities:**
1. **Unit Tests** (70%): Fast, isolated, many
2. **Integration Tests** (20%): Medium speed, test interactions
3. **E2E Tests** (10%): Slow, test critical user flows

### Test Independence

- Tests must be **isolated** and **independent**
- No test should depend on another test's state
- Each test should clean up after itself
- Use fixtures and factories for setup

### Fast Feedback

- Unit tests should run in **milliseconds**
- Integration tests should run in **seconds**
- E2E tests should run in **minutes**
- Developers should run tests locally before pushing

---

## Test Architecture

### Backend Test Structure

```
tests/
├── conftest.py                 # Shared fixtures, pytest configuration
├── factories.py                # Test data factories (factory-boy)
├── fixtures/                   # Database fixture files
│   ├── tournaments.json
│   ├── fencers.json
│   └── events.json
├── unit/                       # Unit tests
│   ├── test_models/           # Core model tests
│   │   ├── test_tournament.py
│   │   ├── test_fencer.py
│   │   ├── test_event.py
│   │   └── ... (all 35+ models)
│   ├── test_services/         # Business logic tests
│   │   ├── test_tournament_service.py
│   │   ├── test_draw_service.py
│   │   └── test_result_service.py
│   └── test_utils/            # Utility function tests
│       └── test_validation.py
├── integration/                # Integration tests
│   ├── test_sync.py           # ✅ (exists)
│   ├── test_repositories.py   # Repository-DB integration
│   ├── test_api_workflows.py  # Full API cycles
│   └── test_cluster_communication.py
└── e2e/                        # End-to-end tests
    ├── test_cluster.py        # ✅ (exists)
    ├── test_full_tournament_workflow.py
    └── test_offline_sync_workflow.py

backend/apps/*/tests/           # Django app-specific tests
├── test_tournament_api.py     # ✅ (exists)
├── test_tournament_status_api.py  # ✅ (exists)
├── test_fencer_api.py
├── test_event_api.py
└── ...
```

### Frontend Test Structure

```
web_frontend/src/
├── __tests__/
│   ├── setup.test.ts          # ✅ (exists)
│   ├── vitest.setup.ts        # Global test setup
│   ├── test-utils.ts          # Vue testing helpers
│   └── mocks/                 # Mock factories
│       ├── mockData.ts        # Test data factories
│       ├── apiMocks.ts        # API response mocks
│       └── storeMocks.ts      # Pinia store mocks
├── components/
│   └── __tests__/             # Component tests
│       ├── TournamentList.test.ts
│       ├── TournamentForm.test.ts
│       ├── PoolGeneration.test.ts
│       └── ... (all components)
├── services/
│   └── __tests__/             # Service tests
│       ├── DataManager.test.ts
│       ├── NetworkService.test.ts
│       └── storage/
│           └── IndexedDBService.test.ts
├── stores/
│   └── __tests__/             # Store tests
│       ├── authStore.test.ts
│       └── syncStore.test.ts
└── utils/
    └── __tests__/             # Utility tests
        └── csrf.test.ts
```

### Desktop Test Structure

```
desktop/tests/
├── setup.ts                    # Electron test utilities
├── unit/
│   ├── ipcHandlers.test.ts     # IPC message tests
│   └── electronBridge.test.ts  # Main/renderer bridge
└── integration/
    └── app.test.ts              # Full app lifecycle
```

---

## Test Categories

### 1. Unit Tests

**Purpose**: Test individual components in isolation

**Backend Examples:**
- Model validation and constraints
- Service business logic
- Repository queries (with mocked DB)
- Utility functions

**Frontend Examples:**
- Component rendering
- Props validation
- Event emission
- Computed properties
- Service data transformation
- Store state management

**Characteristics:**
- **Speed**: < 100ms per test
- **Dependencies**: Mocked
- **Scope**: Single function/class
- **Count**: Many (thousands)

### 2. Integration Tests

**Purpose**: Test component interactions

**Backend Examples:**
- Repository CRUD with real database (SQLite)
- API view request/response cycle
- Service-database integration
- Cluster node synchronization

**Frontend Examples:**
- Component parent-child interactions
- Service calls with mocked backend
- IndexedDB operations
- Store-service integration

**Characteristics:**
- **Speed**: 100ms - 1s per test
- **Dependencies**: Real (database, services)
- **Scope**: Multiple components
- **Count**: Moderate (hundreds)

### 3. End-to-End Tests

**Purpose**: Test critical user workflows

**Backend Examples:**
- Complete tournament lifecycle
- Offline mode → synchronization
- Cluster coordination

**Frontend Examples:**
- User login → tournament creation
- Pool generation → bout recording → rankings
- Offline mode → sync workflow

**Characteristics:**
- **Speed**: > 1s per test
- **Dependencies**: Full stack
- **Scope**: Complete workflows
- **Count**: Few (dozens)

---

## Infrastructure Setup

### Backend Dependencies

Add to `backend/requirements.txt`:

```txt
# Testing dependencies
pytest==8.3.2
pytest-django==4.8.0
pytest-cov==4.1.0           # Coverage reporting
pytest-xdist==3.3.1          # Parallel execution
factory-boy==3.3.0          # Test factories
freezegun==1.4.0            # Date/time mocking
```

### Frontend Dependencies

Add to `web_frontend/package.json` devDependencies:

```json
{
  "devDependencies": {
    "@vitest/coverage-v8": "^1.0.0",
    "@vue/test-utils": "^2.4.0",
    "happy-dom": "^12.0.0",
    "msw": "^2.0.0"
  }
}
```

### Desktop Dependencies

Add to `desktop/package.json` devDependencies:

```json
{
  "devDependencies": {
    "vitest": "^4.1.0",
    "@vitest/coverage-v8": "^1.0.0",
    "@electron/replay": "^1.0.0"
  }
}
```

---

## Writing Tests

### Backend Unit Test Example

```python
# tests/unit/test_models/test_tournament.py
import pytest
from datetime import date, timedelta
from core.models.tournament import Tournament


class TestTournamentModel:
    """Test Tournament domain model"""

    def test_create_valid_tournament(self):
        """Test creating a valid tournament"""
        tournament = Tournament(
            tournament_name="Test Tournament",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )
        
        assert tournament.tournament_name == "Test Tournament"
        assert tournament.status == "PLANNING"
        assert tournament.id is not None

    def test_tournament_default_status(self):
        """Test default status is PLANNING"""
        tournament = Tournament(
            tournament_name="Test",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1)
        )
        
        assert tournament.status == "PLANNING"

    def test_tournament_invalid_dates(self):
        """Test invalid date range raises error"""
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            Tournament(
                tournament_name="Invalid Tournament",
                start_date=date.today(),
                end_date=date.today() - timedelta(days=1)
            )
```

### Backend Integration Test Example

```python
# tests/integration/test_repositories.py
import pytest
from uuid import uuid4
from backend.apps.fencing_organizer.repositories.tournament_repo import DjangoTournamentRepository
from core.models.tournament import Tournament


@pytest.mark.django_db
class TestTournamentRepository:
    """Test Tournament repository with real database"""

    def test_create_and_retrieve_tournament(self):
        """Test creating and retrieving a tournament"""
        repo = DjangoTournamentRepository()
        
        # Create
        tournament_data = {
            "tournament_name": "Test Tournament",
            "start_date": date.today(),
            "end_date": date.today() + timedelta(days=7)
        }
        tournament = repo.create(tournament_data)
        
        # Retrieve
        retrieved = repo.get_by_id(tournament.id)
        
        assert retrieved is not None
        assert retrieved.tournament_name == "Test Tournament"
```

### Frontend Component Test Example

```typescript
// web_frontend/src/components/__tests__/TournamentList.test.ts
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TournamentList from '@/components/tournament/TournamentList.vue'
import { createMockTournament } from '@/__tests__/mocks/mockData'

describe('TournamentList', () => {
  it('should render list of tournaments', () => {
    const tournaments = [
      createMockTournament({ id: '1', tournament_name: 'Tournament 1' }),
      createMockTournament({ id: '2', tournament_name: 'Tournament 2' })
    ]

    const wrapper = mount(TournamentList, {
      props: { tournaments }
    })

    expect(wrapper.findAll('.tournament-item')).toHaveLength(2)
    expect(wrapper.text()).toContain('Tournament 1')
    expect(wrapper.text()).toContain('Tournament 2')
  })

  it('should emit edit event when edit button clicked', async () => {
    const tournament = createMockTournament()
    const wrapper = mount(TournamentList, {
      props: { tournaments: [tournament] }
    })

    await wrapper.find('.edit-button').trigger('click')

    expect(wrapper.emitted('edit')).toBeTruthy()
    expect(wrapper.emitted('edit')[0]).toEqual([tournament])
  })
})
```

### Frontend Service Test Example

```typescript
// web_frontend/src/services/__tests__/DataManager.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { DataManager } from '@/services/DataManager'
import { mockFetchResponse } from '@/__tests__/test-utils'

describe('DataManager', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createTournament', () => {
    it('should create tournament successfully', async () => {
      const mockTournament = {
        id: '1',
        tournament_name: 'Test Tournament'
      }
      mockFetchResponse(mockTournament, true)

      const result = await DataManager.createTournament({
        tournament_name: 'Test Tournament',
        date_range: ['2024-01-01', '2024-01-07']
      })

      expect(result).toEqual(mockTournament)
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/tournaments/',
        expect.objectContaining({ method: 'POST' })
      )
    })

    it('should handle creation error', async () => {
      mockFetchResponse({ error: 'Validation failed' }, false)

      const result = await DataManager.createTournament({})

      expect(result).toBeNull()
    })
  })
})
```

---

## Test Utilities

### Backend Test Factories

Use `factory-boy` to create test data:

```python
# tests/factories.py
import factory
from factory.django import DjangoModelFactory
from datetime import date, timedelta
from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament
from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer


class TournamentFactory(DjangoModelFactory):
    """Factory for creating Tournament instances"""
    
    class Meta:
        model = DjangoTournament
    
    tournament_name = factory.Sequence(lambda n: f'Tournament {n}')
    start_date = factory.LazyFunction(date.today)
    end_date = factory.LazyFunction(lambda: date.today() + timedelta(days=7))
    status_id = 1  # PLANNING status


class FencerFactory(DjangoModelFactory):
    """Factory for creating Fencer instances"""
    
    class Meta:
        model = DjangoFencer
    
    first_name = factory.Sequence(lambda n: f'Fencer{n}')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(lambda obj: f'{obj.first_name.lower()}@example.com')


# Usage in tests
def test_with_factory():
    tournament = TournamentFactory()
    fencers = FencerFactory.create_batch(10)
    # ...
```

### Backend Fixtures

```python
# tests/conftest.py
import pytest
from tests.factories import TournamentFactory, FencerFactory


@pytest.fixture
def sample_tournament():
    """Create a sample tournament"""
    return TournamentFactory()


@pytest.fixture
def tournament_with_fencers():
    """Create a tournament with fencers"""
    tournament = TournamentFactory()
    fencers = FencerFactory.create_batch(12, tournament=tournament)
    return tournament, fencers


@pytest.fixture
def admin_client(client, admin_user):
    """Pre-authenticated admin client"""
    client.force_login(admin_user)
    return client


@pytest.fixture
def api_client():
    """DRF API client"""
    from rest_framework.test import APIClient
    return APIClient()
```

### Frontend Mock Factories

```typescript
// web_frontend/src/__tests__/mocks/mockData.ts
import type { Tournament } from '@/types/tournament'
import type { Fencer } from '@/types/fencer'

let idCounter = 1

export function createMockTournament(overrides: Partial<Tournament> = {}): Tournament {
  return {
    id: String(idCounter++),
    tournament_name: 'Test Tournament',
    organizer: 'Test Organizer',
    location: 'Test Location',
    start_date: '2024-01-01',
    end_date: '2024-01-07',
    status: 'PLANNING',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides
  }
}

export function createMockFencer(overrides: Partial<Fencer> = {}): Fencer {
  return {
    id: String(idCounter++),
    first_name: 'John',
    last_name: 'Doe',
    email: 'john@example.com',
    club: 'Test Club',
    nationality: 'USA',
    ...overrides
  }
}

export function createMockTournamentList(count: number): Tournament[] {
  return Array.from({ length: count }, (_, i) =>
    createMockTournament({ id: String(i + 1), tournament_name: `Tournament ${i + 1}` })
  )
}
```

### Frontend Test Utilities

```typescript
// web_frontend/src/__tests__/test-utils.ts
import { render } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import type { Component } from 'vue'

/**
 * Render a component with Pinia store
 */
export function renderWithPinia(component: Component, options: Record<string, any> = {}) {
  setActivePinia(createPinia())
  return render(component, options)
}

/**
 * Render a component with Vue Router
 */
export function renderWithRouter(component: Component, options: Record<string, any> = {}) {
  const router = createRouter({
    history: createWebHistory(),
    routes: []
  })
  
  return render(component, {
    global: {
      plugins: [router],
      ...options.global
    }
  })
}

/**
 * Mock fetch response
 */
export function mockFetchResponse(data: any, ok: boolean = true) {
  ;(global.fetch as any) = vi.fn(() =>
    Promise.resolve({
      ok,
      json: () => Promise.resolve(data)
    })
  )
}

/**
 * Mock offline state
 */
export function mockOfflineState(isOffline: boolean = true) {
  Object.defineProperty(navigator, 'onLine', {
    writable: true,
    value: !isOffline
  })
}
```

---

## Running Tests

### Backend Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_models/test_tournament.py

# Run specific test class
pytest tests/unit/test_models/test_tournament.py::TestTournamentModel

# Run specific test
pytest tests/unit/test_models/test_tournament.py::TestTournamentModel::test_create_valid_tournament

# Run with coverage
pytest --cov=core --cov=backend --cov-report=html

# Run specific test category
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e           # E2E tests only

# Run in parallel
pytest -n auto          # Use all CPUs

# Run tests matching pattern
pytest -k "tournament"  # Tests with "tournament" in name
```

### Frontend Tests

```bash
# Navigate to frontend directory
cd web_frontend

# Run all tests
npm run test

# Run in watch mode
npm run test -- --watch

# Run specific test file
npm run test -- src/components/__tests__/TournamentList.test.ts

# Run with coverage
npm run test -- --coverage

# Run tests matching pattern
npm run test -- -t "TournamentList"

# Run with UI
npm run test -- --ui
```

### Desktop Tests

```bash
# Navigate to desktop directory
cd desktop

# Run all tests
npm run test

# Run with coverage
npm run test -- --coverage
```

### Run All Tests

```bash
# Run backend + frontend tests
npm run test:all

# Or manually
pytest && cd web_frontend && npm run test && cd ../desktop && npm run test
```

---

## Coverage Requirements

### Minimum Coverage Thresholds

| Layer        | Statements | Branches | Functions | Lines |
|--------------|-----------|----------|-----------|-------|
| **Core Models**   | 90%       | 85%      | 90%       | 90%   |
| **Backend Services** | 85%    | 80%      | 85%       | 85%   |
| **Backend APIs**  | 80%       | 75%      | 80%       | 80%   |
| **Frontend Services** | 80%   | 75%      | 80%       | 80%   |
| **Frontend Components** | 75% | 70%      | 75%       | 75%   |
| **Overall**       | 75%       | 70%      | 75%       | 75%   |

### Coverage Configuration

**Backend (pytest.ini):**
```ini
[pytest]
addopts = 
    --cov=core 
    --cov=backend 
    --cov-report=term-missing 
    --cov-report=html 
    --cov-fail-under=75
```

**Frontend (vitest.config.ts):**
```typescript
test: {
  coverage: {
    provider: 'v8',
    reporter: ['text', 'html', 'lcov'],
    statements: 75,
    branches: 70,
    functions: 75,
    lines: 75
  }
}
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/_test.yml
name: Run Tests

on:
  workflow_call:

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-django pytest-cov factory-boy
      
      - name: Run backend tests
        run: pytest tests/ -v --cov=core --cov=backend --cov-report=xml --cov-fail-under=75
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: backend

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      
      - name: Install dependencies
        working-directory: ./web_frontend
        run: npm ci
      
      - name: Run frontend tests
        working-directory: ./web_frontend
        run: npm run test -- --run --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./web_frontend/coverage/lcov.info
          flags: frontend
```

### Pre-commit Hooks

```bash
#!/bin/bash
# scripts/pre-commit.sh

# Frontend lint
cd web_frontend && npm run lint || exit 1

# Backend lint
flake8 backend/ core/ tests/ --exclude=venv,migrations,__pycache__ || exit 1
black backend/ core/ tests/ --check --exclude="venv|migrations" || exit 1

# Run affected tests
pytest tests/ -k "test_$(git diff --name-only HEAD~1 | grep '.py' | head -1)" || exit 1
```

---

## Best Practices

### General Principles

1. **Write Tests First (TDD)**
   - Write failing test → Write code → Make test pass
   - Tests document expected behavior

2. **Keep Tests Simple**
   - One concept per test
   - Arrange-Act-Assert pattern
   - Avoid test logic

3. **Use Descriptive Names**
   - `test_create_tournament_with_valid_data`
   - Not: `test_tournament_1`

4. **Independent Tests**
   - No shared state
   - Each test cleans up
   - Order doesn't matter

5. **Test Edge Cases**
   - Valid inputs
   - Invalid inputs
   - Boundary conditions
   - Error conditions

### Backend Best Practices

```python
# Good: Clear, focused test
def test_create_tournament_with_valid_data(self):
    tournament = Tournament(
        tournament_name="Test",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=7)
    )
    assert tournament.status == "PLANNING"

# Better: Use factory
def test_create_tournament_with_valid_data(self):
    tournament = TournamentFactory()
    assert tournament.status == "PLANNING"

# Best: Test behavior, not implementation
@pytest.mark.django_db
def test_tournament_repository_creates_and_retrieves(self):
    repo = DjangoTournamentRepository()
    created = repo.create({"name": "Test"})
    retrieved = repo.get_by_id(created.id)
    assert retrieved.name == "Test"
```

### Frontend Best Practices

```typescript
// Good: Test component behavior
it('should display tournament name', () => {
  const wrapper = mount(TournamentCard, {
    props: { tournament: createMockTournament() }
  })
  expect(wrapper.text()).toContain('Test Tournament')
})

// Better: Test user interaction
it('should emit edit event when clicked', async () => {
  const wrapper = mount(TournamentCard, {
    props: { tournament: createMockTournament() }
  })
  await wrapper.find('.edit-button').trigger('click')
  expect(wrapper.emitted('edit')).toBeTruthy()
})

// Best: Test accessibility
it('should be accessible', () => {
  const wrapper = mount(TournamentCard, {
    props: { tournament: createMockTournament() }
  })
  expect(wrapper.find('button').attributes('aria-label')).toBeDefined()
})
```

### Don'ts

❌ **Don't test implementation details**
```typescript
// Bad: Tests internal state
expect(wrapper.vm.internalState).toBe('foo')

// Good: Tests behavior
expect(wrapper.find('.result').text()).toBe('foo')
```

❌ **Don't use sleep/wait in tests**
```python
# Bad: Flaky, slow
time.sleep(5)

# Good: Wait for condition
def wait_for_condition():
    return tournament.status == 'COMPLETED'
```

❌ **Don't skip tests**
```python
# Bad
@pytest.mark.skip
def test_critical_feature():
    pass

# Good: Fix or delete
def test_critical_feature():
    # Actual test
    pass
```

---

## Troubleshooting

### Common Backend Issues

**Issue: Database locked errors**
```python
# Solution: Use pytest-django's db marker
@pytest.mark.django_db
def test_my_test():
    # Test code
    pass
```

**Issue: Tests affecting each other**
```python
# Solution: Use fixtures with proper scope
@pytest.fixture(scope='function')
def clean_database(db):
    yield
    DjangoTournament.objects.all().delete()
```

**Issue: Slow tests**
```bash
# Solution: Run tests in parallel
pytest -n auto

# Or tag slow tests
@pytest.mark.slow
def test_slow_operation():
    pass

# Skip slow tests during development
pytest -m "not slow"
```

### Common Frontend Issues

**Issue: Component not rendering**
```typescript
// Solution: Ensure proper imports and stubs
const wrapper = mount(MyComponent, {
  global: {
    components: { SomeGlobalComponent },
    stubs: { SomeChildComponent: true }
  }
})
```

**Issue: Fetch not mocked**
```typescript
// Solution: Mock fetch in test setup
beforeEach(() => {
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockData)
    })
  )
})
```

**Issue: Pinia store not initialized**
```typescript
// Solution: Create Pinia instance before test
import { createPinia, setActivePinia } from 'pinia'

beforeEach(() => {
  setActivePinia(createPinia())
})
```

### Performance Tips

**Backend:**
- Use `pytest-xdist` for parallel execution
- Use in-memory SQLite for tests
- Minimize database queries with `select_related`/`prefetch_related`
- Use fixtures with appropriate scope

**Frontend:**
- Use `happy-dom` instead of `jsdom` (faster)
- Mock large dependencies
- Use `vi.mock` for module mocking
- Run specific tests during development

---

## Appendix

### Test Markers (Backend)

```python
# pytest markers
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # Tests with database/services
@pytest.mark.e2e           # End-to-end tests
@pytest.mark.slow          # Long-running tests
@pytest.mark.django_db     # Requires database
```

### Coverage Reports

**Backend:**
```bash
pytest --cov=core --cov=backend --cov-report=html
open htmlcov/index.html
```

**Frontend:**
```bash
npm run test -- --coverage
open coverage/index.html
```

### Useful Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-django Documentation](https://pytest-django.readthedocs.io/)
- [factory-boy Documentation](https://factoryboy.readthedocs.io/)
- [Vitest Documentation](https://vitest.dev/)
- [Vue Test Utils](https://test-utils.vuejs.org/)
- [Testing Library](https://testing-library.com/)

---

**Last Updated**: 2026-04-01  
**Version**: 1.0  
**Authors**: PisteMaster Team