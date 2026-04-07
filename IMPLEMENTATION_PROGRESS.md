# Cluster Sync Implementation Progress

## ✅ Files Created/Modified

### 1. Core Infrastructure Files

**Created:**
- `core/models/versioning.py` - VersionedModel base class for domain models
- `backend/apps/fencing_organizer/models/base.py` - VersionedModel abstract Django model
- `core/models/mapper_base.py` - Helper functions for version fields in mappers
- `backend/apps/fencing_organizer/viewsets/base.py` - SyncWriteModelViewSet with metaclass
- `backend/apps/fencing_organizer/serializers/base.py` - Updated with VersionedModelSerializer
- `backend/apps/fencing_organizer/migrations/0019_add_version_tracking.py` - Migration for version fields

**Modified:**
- `backend/PisteMaster/settings/base.py` - Added middleware and proxy settings
- `backend/apps/cluster/decorators/transaction.py` - Track last_sync_id
- `backend/apps/cluster/apps.py` - Register models with SyncManager

## 📋 Manual Work Required

You need to manually update the following files (programmatic approach would risk errors):

### 1. Domain Models (core/models/)

Update each domain model to inherit from `VersionedModel`:

```python
# core/models/tournament.py
from core.models.versioning import VersionedModel  # ADD THIS IMPORT

@dataclass
class Tournament(VersionedModel):  # CHANGE: Inherit from VersionedModel
    tournament_name: str
    start_date: date
    end_date: date
    # ... other fields ...
    # version, last_modified_node, last_modified_at are INHERITED
```

**Files to update:**
- `core/models/tournament.py`
- `core/models/event.py`
- `core/models/fencer.py`
- `core/models/pool.py`
- `core/models/pool_bout.py`
- `core/models/piste.py`
- `core/models/rule.py`
- `core/models/pool_assignment.py`
- `core/models/event_participant.py`

### 2. Django Models (backend/apps/fencing_organizer/modules/*/models.py)

Update each Django model to include version fields:

```python
# backend/apps/fencing_organizer/modules/tournament/models.py
# ADD these three fields to each model:
class DjangoTournament(models.Model):
    # ... existing fields ...
    
    # ADD THESE FIELDS:
    version = models.BigIntegerField(default=1)
    last_modified_node = models.CharField(max_length=100, blank=True, default='')
    last_modified_at = models.DateTimeField(auto_now=True)
    
    # ... rest of model ...
```

**Files to update:**
- `modules/tournament/models.py` - DjangoTournament
- `modules/event/models.py` - DjangoEvent
- `modules/fencer/models.py` - DjangoFencer
- `modules/pool/models.py` - DjangoPool
- `modules/pool_bout/models.py` - DjangoPoolBout
- `modules/piste/models.py` - DjangoPiste
- `modules/rule/models.py` - DjangoRule
- `modules/pool_assignment/models.py` - DjangoPoolAssignment
- `modules/event_participant/models.py` - DjangoEventParticipant

### 3. Serializers (backend/apps/fencing_organizer/modules/*/serializers.py)

Update each serializer to inherit from `VersionedModelSerializer`:

```python
# backend/apps/fencing_organizer/modules/tournament/serializers.py
from backend.apps.fencing_organizer.serializers.base import VersionedModelSerializer  # CHANGE IMPORT

class TournamentSerializer(VersionedModelSerializer):  # CHANGE: Inherit from VersionedModelSerializer
    class Meta:
        model = DjangoTournament
        fields = '__all__'  # Version fields are automatically included
```

**Files to update:**
- `modules/tournament/serializers.py`
- `modules/event/serializers.py`
- `modules/fencer/serializers.py`
- `modules/pool/serializers.py`
- `modules/pool_bout/serializers.py`
- `modules/piste/serializers.py`
- `modules/rule/serializers.py`
- `modules/pool_assignment/serializers.py`
- `modules/event_participant/serializers.py`

### 4. Mappers (backend/apps/fencing_organizer/mappers/)

Add version field handling using helperfunctions:

```python
# backend/apps/fencing_organizer/mappers/tournament_mapper.py
from core.models.mapper_base import versioned_fields_to_dict, versioned_fields_from_dict  # ADD

class TournamentMapper:
    @staticmethod
    def to_domain(django_model: DjangoTournament) -> Tournament:
        version_fields = versioned_fields_to_dict(django_model)  # ADD
        return Tournament(
            id=django_model.id,
            tournament_name=django_model.tournament_name,
            # ... other fields ...
            **version_fields  # ADD: Include version fields
        )
    
    @staticmethod
    def to_django(domain_model: Tournament) -> DjangoTournament:
        django_model = DjangoTournament(
            id=domain_model.id,
            tournament_name=domain_model.tournament_name,
            # ... other fields ...
        )
        versioned_fields_from_dict(domain_model.__dict__, django_model)  # ADD
        return django_model
```

**Files to update:**
- `mappers/tournament_mapper.py`
- `mappers/event_mapper.py`
- `mappers/fencer_mapper.py`
- `mappers/pool_mapper.py`
- `mappers/pool_bout_mapper.py`
- `mappers/piste_mapper.py`
- `mappers/rule_mapper.py`
- `mappers/pool_assignment_mapper.py`
- `mappers/event_participant_mapper.py`

### 5. ViewSets (backend/apps/fencing_organizer/modules/*/viewsets.py)

Update each viewset to inherit from `SyncWriteModelViewSet`:

```python
# backend/apps/fencing_organizer/modules/tournament/viewsets.py
from backend.apps.fencing_organizer.viewsets.base import SyncWriteModelViewSet  # CHANGE IMPORT

class TournamentViewSet(SyncWriteModelViewSet):  # CHANGE: Inherit from SyncWriteModelViewSet
    sync_table_name = 'tournament'  # ADD: This enables sync logging
    queryset = DjangoTournament.objects.all()
    serializer_class = TournamentSerializer
    # ... rest remains the same ...
```

**Files to update:**
- `modules/tournament/viewsets.py`
- `modules/event/viewsets.py`
- `modules/fencer/viewsets.py`
- `modules/pool/viewsets.py`
- `modules/pool_bout/viewsets.py`
- `modules/piste/viewsets.py`
- `modules/rule/viewsets.py`
- `modules/pool_assignment/viewsets.py`
- `modules/event_participant/viewsets.py`

## 🚀Steps to Complete

### Step 1: Apply Database Migration

```bash
cd backend
source ../venv/bin/activate
python manage.py migrate
```

This will add version fields to all database tables.

### Step 2: Update Domain Models(Manual)

For each domain model file in `core/models/`:

1. Add import: `from core.models.versioning import VersionedModel`
2. Change class declaration: `class Tournament(VersionedModel):`
3. Remove any existing `version`, `last_modified_node`, `last_modified_at` fields

### Step 3: Update Django Models (Manual)

For each Django model file in `backend/apps/fencing_organizer/modules/*/models.py`:

1. Add these three fields before `created_at`:
```python
version = models.BigIntegerField(default=1)
last_modified_node = models.CharField(max_length=100, blank=True, default='')
last_modified_at = models.DateTimeField(auto_now=True)
```

### Step 4: Update Serializers (Manual)

For each serializer file in `backend/apps/fencing_organizer/modules/*/serializers.py`:

1. Change import: `from rest_framework import serializers` to 
   `from backend.apps.fencing_organizer.serializers.base import VersionedModelSerializer`
2. Change base class: `class TournamentSerializer(serializers.ModelSerializer):` to
   `class TournamentSerializer(VersionedModelSerializer):`

### Step 5: Update Mappers (Manual)

For each mapper file in `backend/apps/fencing_organizer/mappers/`:

1. Add imports:
```python
from core.models.mapper_base import versioned_fields_to_dict, versioned_fields_from_dict
```

2. In `to_domain()`: Add `**version_fields` to constructor
3. In `to_django()`: Call `versioned_fields_from_dict(domain.__dict__, django_model)`

### Step 6: Update ViewSets (Manual)

For each viewset file in `backend/apps/fencing_organizer/modules/*/viewsets.py`:

1. Add import:
```python
from backend.apps.fencing_organizer.viewsets.base import SyncWriteModelViewSet
```

2. Change base class and add sync_table_name:
```python
class TournamentViewSet(SyncWriteModelViewSet):  # Changedfrom ModelViewSet
    sync_table_name = 'tournament'  # Add this line
    queryset = DjangoTournament.objects.all()
    serializer_class = TournamentSerializer
    # ... rest stays the same ...
```

## 🧪 Testing

### Test 1: Check Migration

```bash
cd backend
python manage.py showmigrations fencing_organizer
# Should show [X] 0019_add_version_tracking

python manage.py dbshell
sqlite> .schema djangotournament
# Should show version, last_modified_node, last_modified_at columns
```

### Test 2: Test SyncLogging

```bash
# Create a tournament via API
curl -X POST http://localhost:8000/api/tournaments/ \
  -H "Content-Type: application/json" \
  -d '{"tournament_name": "Test", "start_date": "2025-01-01", "end_date": "2025-01-02"}'

# Check sync log
sqlite> SELECT * FROM sync_log;
# Should see INSERT entry with tournament data

# Check version fields
sqlite> SELECT id, tournament_name, version FROM tournament;
# version should be 1
```

### Test 3: Test Cluster Sync

1. Start two nodes:
```bash
# Node 1 (Master)
DJANGO_DB_PATH=db_node1.sqlite3 python manage.py runserver 8000

# Node 2 (Follower)
DJANGO_DB_PATH=db_node2.sqlite3 python manage.py runserver 8001
```

2. Configure in Electron:
- Node 1: `mode: 'cluster', isMaster: true, apiPort: 8000`
- Node 2: `mode: 'cluster', isMaster: false, masterIp: 'localhost', apiPort: 8001`

3. Create tournament on Node 1

4. Check Node 2 syncs:
```bash
curl http://localhost:8001 api/tournaments/
# Should show the tournament created on Node 1
```

## 📊 Summary

**Files Created:** 6
**Files Modified:** 3
**Manual Updates Required:** 
- 9 domain models
- 9 Django models
- 9 serializers
- 9 mappers
- 9 viewsets
- 1 migration (created, needs to be applied)

**Estimated Time:**2-3 hours for manual updates

## ⚠️ Important Notes

1. **Backup your database before applying migration**
2. **Test migration on st aging first**
3. **Version fields are auto-managed** - don't set them manually
4. **All custom actions that modify data need manual sync logging** - add `@auto_sync_write('table_name')` decorator
5. **Read-only operations (GET)** don't need changes

## 🔄 Rollback

If issues occur, rollback:

```bash
python manage.py migrate fencing_organizer 0018
```

And comment out the middleware in settings:
```python
# "backend.apps.cluster.middleware.api_router.ApiRouterMiddleware",
# "backend.apps.cluster.middleware.write_sync.SyncWriteMiddleware",
```

## 📝 Next Steps After Manual Updates

1. Run tests: `pytest tests/`
2. Create tournament and verify sync log
3. Test two-node cluster
4. Test follower proxy to master
5. Test ACK timeout handling

---

Generated: 2026-04-07
Implementation Phase: Files Created, Awaiting Manual Updates