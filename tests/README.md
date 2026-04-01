# PisteMaster Test Infrastructure

This directory contains the comprehensive test suite for the PisteMaster fencing tournament management system.

## Directory Structure

```
tests/
├── conftest.py                    # Global pytest configuration
├── fixtures.py                    # Reusable pytest fixtures
├── factories.py                   # Domain model test factories
├── django_factories.py            # Django model test factories
├── unit/                          # Unit tests
│   ├── test_factories/           # Factory tests
│   ├── test_models/              # Core model unit tests
│   └── test_services/            # Service layer tests
├── integration/                   # Integration tests
│   └── test_sync.py              # Sync integration tests
└── e2e/                           # End-to-end tests
    └── test_cluster.py           # Cluster E2E tests
```

## Test Dependencies

### Backend (Python)

- `pytest==8.3.2` - Testing framework
- `pytest-django==4.8.0` - Django test utilities
- `pytest-cov==5.0.0` - Coverage reporting
- `factory-boy==3.3.0` - Test data factories
- `faker==26.0.0` - Fake data generator

### Frontend (TypeScript)

- `vitest==4.1.0` - Testing framework
- `@vitest/coverage-v8==4.1.0` - Coverage reporting
- `@vitest/ui==4.1.0` - Visual test UI
- `@vue/test-utils==2.4.0` - Vue component testing
- `jsdom==26.0.0` - DOM environment
- `@faker-js/faker==9.0.0` - Fake data generator

### Desktop (Electron)

- `vitest==4.1.0` - Testing framework
- `@vitest/coverage-v8==4.1.0` - Coverage reporting
- `@vue/test-utils==2.4.0` - Vue component testing
- `jsdom==26.0.0` - DOM environment
- `@faker-js/faker==9.0.0` - Fake data generator

## Running Tests

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=backend --cov-report=html

# Run specific test file
pytest tests/unit/test_factories/test_factories.py

# Run specific test class
pytest tests/unit/test_factories/test_factories.py::TestDomainModelFactories

# Run specific test method
pytest tests/unit/test_factories/test_factories.py::TestDomainModelFactories::test_tournament_factory

# Run with verbose output
pytest -v tests/unit/test_factories/

# Run tests matching a pattern
pytest -k "tournament" tests/

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run only E2E tests
pytest tests/e2e/
```

### Frontend Tests

```bash
cd web_frontend

# Run all tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run tests with UI
npm run test:ui

# Run specific test file
npx vitest run path/to/test.spec.ts
```

### Desktop Tests

```bash
cd desktop

# Run all tests
npm run test

# Run tests with coverage
npm run test:coverage
```

## Test Factories

### Domain Model Factories (core/models/)

Located in `tests/factories.py`:

- `TournamentFactory` - Create Tournament domain models
- `FencerFactory` - Create Fencer domain models
- `EventFactory` - Create Event domain models
- `PoolFactory` - Create Pool domain models
- `PoolBoutFactory` - Create PoolBout domain models
- `MatchFactory` - Create Match domain models
- `PisteFactory` - Create Piste domain models
- `RefereeFactory` - Create Referee domain models
- `SyncLogFactory` - Create SyncLog domain models
- `SyncStateFactory` - Create SyncState domain models

Helper functions:
- `create_tournament_with_events()` - Create tournament with events
- `create_pool_with_fencers()` - Create pool with fencers
- `create_match_with_fencers()` - Create match with fencers
- `create_tournament_full_setup()` - Create complete tournament setup

### Django Model Factories (backend/apps/)

Located in `tests/django_factories.py`:

- `UserFactory` - Create User Django models
- `DjangoTournamentFactory` - Create DjangoTournament ORM models
- `DjangoFencerFactory` - Create DjangoFencer ORM models

### Usage Examples

```python
# Domain model factories
from tests.factories import TournamentFactory, FencerFactory

tournament = TournamentFactory()
fencers = [FencerFactory() for _ in range(10)]

# Django model factories (requires @pytest.mark.django_db)
from tests.django_factories import UserFactory, DjangoTournamentFactory

user = UserFactory(username='admin', password='secret')
tournament = DjangoTournamentFactory(created_by=user)

# Fixture usage
def test_tournament_creation(tournament):
    assert tournament.tournament_name is not None
    assert tournament.status == "PLANNING"
```

## Pytest Fixtures

Common fixtures are defined in `tests/fixtures.py`:

### Single Entity Fixtures
- `tournament` - Single tournament
- `fencer` - Single fencer
- `event` - Single event (with tournament)
- `pool` - Single pool (with event)
- `match` - Single match (with event)
- `piste` - Single piste (with tournament)
- `referee` - Single referee

### Multiple Entity Fixtures
- `multiple_fencers` - List of 5 fencers
- `multiple_tournaments` - List of 3 tournaments
- `multiple_events` - List of 3 events (same tournament)

### Complex Setup Fixtures
- `tournament_setup` - Complete setup (tournament, events, pistes, fencers, pools, referees)
- `pool_with_fencers` - Pool with 6 fencers
- `match_with_fencers` - Match with two fencers

### Sync Test Fixtures
- `sync_logs` - Multiple sync logs (INSERT, UPDATE, DELETE)
- `sync_states` - Multiple sync states (different nodes)

## Test Coverage

Coverage requirements (defined in `pyproject.toml`):
- Overall: **75% minimum**
- Core models: **90%+**
- Core services: **85%+**
- Backend APIs: **80%+**

## Writing New Tests

### Unit Test Template

```python
"""
Unit tests for [module name].
"""

import pytest
from datetime import date

from core.models.tournament import Tournament
from tests.factories import TournamentFactory


class TestTournament:
    """Test suite for Tournament model."""

    def test_tournament_creation(self):
        """Test creating a tournament."""
        tournament = TournamentFactory()
        assert tournament.id is not None
        assert tournament.status == "PLANNING"

    def test_tournament_to_dict(self):
        """Test tournament serialization."""
        tournament = TournamentFactory()
        tournament_dict = tournament.to_dict()
        assert "id" in tournament_dict
        assert "tournament_name" in tournament_dict

    @pytest.mark.parametrize("status", ["PLANNING", "ONGOING", "COMPLETED"])
    def test_tournament_status_transitions(self, status):
        """Test different tournament statuses."""
        tournament = TournamentFactory(status=status)
        assert tournament.status == status
```

### Integration Test Template

```python
"""
Integration tests for [feature name].
"""

import pytest
from tests.django_factories import UserFactory, DjangoTournamentFactory


@pytest.mark.django_db
class TestTournamentAPI:
    """Integration tests for Tournament API."""

    def test_create_tournament_via_api(self, client):
        """Test creating tournament via API."""
        user = UserFactory()
        client.force_authenticate(user=user)
        
        response = client.post('/api/tournaments/', {
            'tournament_name': 'Test Tournament',
            'start_date': '2024-01-01',
            'end_date': '2024-01-07',
        })
        
        assert response.status_code == 201
        assert response.data['tournament_name'] == 'Test Tournament'
```

## Best Practices

1. **Use fixtures** - Prefer fixtures over creating data manually
2. **Use factories** - Use factories for creating test data
3. **Test in isolation** - Each test should be independent
4. **Follow AAA pattern** - Arrange, Act, Assert
5. **Use descriptive names** - Test names should describe what is being tested
6. **Test edge cases** - Not just the happy path
7. **Mock external dependencies** - Don't rely on external services
8. **Clean up** - Ensure tests don't leave side effects

## Continuous Integration

Tests run automatically on:
- Push to main/master branches
- Pull request creation
- Pre-commit hooks (see `scripts/pre-commit.sh`)

CI workflow: `.github/workflows/_test.yml`

## Code Style

Tests should follow the same code style as the main codebase:
- Python: Black formatting, flake8 linting
- TypeScript: Prettier formatting, ESLint linting

## Further Reading

- [Testing Guide](../docs/testing-guide.md) - Comprehensive testing documentation
- [Pytest Documentation](https://docs.pytest.org/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [Vue Test Utils](https://test-utils.vuejs.org/)