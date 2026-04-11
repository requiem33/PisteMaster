# Distributed Cluster Architecture for PisteMaster

## 1. Overview

### 1.1 Background

PisteMaster serves large-scale fencing tournament organization scenarios, supporting 1000+ athletes, 10+ events, and 100+ groups running simultaneously. Multiple clients (referees, organizers, display screens) need to collaborate on group assignments, score entry, and ranking calculations.

The system operates in a LAN environment without a central server, relying only on standard Windows PCs, with flexible switching between single-node and cluster modes.

### 1.2 Goals

- **High Availability**: Automatic failover when the master node fails
- **Data Consistency**: Synchronous write confirmation ensures critical data is replicated before acknowledging success
- **Simplified Deployment**: No external dependencies (etcd, Redis, etc.) - only UDP broadcast for discovery
- **Offline Capability**: Frontend IndexedDB cache enables offline operation

### 1.3 Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Service Discovery | UDP Broadcast | Lightweight, no external dependencies, sufficient for LAN |
| Write Consistency | Synchronous Confirmation | Critical data (scores) must not be lost during failover |
| Partition Tolerance | Availability Priority | In split-brain scenarios, both partitions continue serving; manual resolution on recovery |
| Leader Election | Bully Algorithm | Simple, deterministic election based on node ID |

---

## 2. Architecture Overview

### 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      LAN (Gigabit Switch)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Master Node (Electron + Django)                  │  │
│  │  - Processes all write requests (POST/PUT/DELETE)            │  │
│  │  - Writes to local SQLite + sync_log                         │  │
│  │  - Notifies followers via HTTP POST /sync/notify/             │  │
│  │  - Provides incremental/full sync API                        │  │
│  │  - Waits for replica ACK before responding to client          │  │
│  │  - Broadcasts heartbeat via UDP                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│         │                            ▲                              │
│         │ HTTP /sync/notify/          │ HTTP /sync/ack/             │
│         │ (push notification)         │ (acknowledgement)           │
│         ▼                            │                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐         │
│  │ Follower A    │  │ Follower B    │  │ Follower C    │         │
│  │ - Read-only   │  │ - Read-only   │  │ - Read-only   │         │
│  │ - Local SQLite│  │ - Local SQLite│  │ - Local SQLite│         │
│  │ - SyncWorker  │  │ - SyncWorker  │  │ - SyncWorker  │         │
│  │   (pull sync) │  │   (pull sync) │  │   (pull sync) │         │
│  │ - ACK writes  │  │ - ACK writes  │  │ - ACK writes  │         │
│  │ - Monitor HB  │  │ - Monitor HB  │  │ - Monitor HB  │         │
│  │ - Notify EP   │  │ - Notify EP   │  │ - Notify EP   │         │
│  └───────────────┘  └───────────────┘  └───────────────┘         │
│         │                            ▲                              │
│         │ HTTP /sync/changes/         │ (reads local SQLite)       │
│         └────────────────────────────┘                              │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │         Service Discovery (UDP Broadcast Port 9000)           │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Core Components

| Component | Responsibility | Location |
|-----------|---------------|----------|
| **NodeDiscovery** | UDP-based node discovery, heartbeat, election | Backend (Python) |
| **HeartbeatMonitor** | Monitor master heartbeat, trigger failover | Backend (Python) |
| **SyncManager** | Change log recording, incremental/full sync, apply changes | Backend (Python) |
| **SyncWorker** | Background thread that pulls changes from master on followers | Backend (Python) |
| **SyncLog Model** | Persist change records in SQLite | Backend (Django Model) |
| **SyncState Model** | Track each node's sync progress (last_synced_id, url) | Backend (Django Model) |
| **ApiRouter** | Route requests based on node role (master/follower) | Backend (Django Middleware) |
| **SyncWriteMiddleware** | Intercept writes, notify followers, wait for ACKs | Backend (Django Middleware) |
| **AckQueue** | Track pending ACKs from followers for synchronous writes | Backend (Python, threading.Event) |
| **FollowerProxy** | Notify followers of new changes via HTTP /sync/notify/ | Backend (Python) |
| **ConflictResolver** | Resolve conflicts after network partition recovery | Frontend (TypeScript) |
| **SyncQueueService** | Offline operation queue with retry | Frontend (TypeScript) |
| **IndexedDB Cache** | Local data cache with offline-first reads | Frontend (IndexedDB) |

---

## 3. Startup Modes and Node Roles

### 3.1 Single-Node Mode

- No network coordination, all APIs processed locally
- Suitable for small tournaments or demo environments
- Configuration: `mode = "single"`

### 3.2 Cluster Mode

- Automatic node discovery and election on startup
- Master handles all writes, followers provide read-only APIs
- Synchronous write confirmation to replicas
- Configuration: `mode = "cluster"`

### 3.3 Node Roles

| Role | Write Requests | Read Requests | Special Duties |
|------|---------------|---------------|----------------|
| **Master** | Process locally | Process locally | Record sync_log, notify followers via /sync/notify/, wait for ACKs, broadcast heartbeat |
| **Follower** | Proxy/Reject (503) | Process locally | Pull sync (SyncWorker), ACK writes, monitor heartbeat, listen for /sync/notify/ |

---

## 4. Service Discovery and Election

### 4.1 UDP Broadcast Protocol

**Transport**: UDP broadcast to `255.255.255.255:9000`

**Message Types**:

```json
{
  "type": "announce",
  "node_id": "PC01_abc12345",
  "ip": "192.168.1.100",
  "port": 8000,
  "timestamp": 1620000000,
  "is_master": false,
  "version": 1
}
```

| Type | Direction | Frequency | Purpose |
|------|-----------|-----------|---------|
| `announce` | All nodes | 3x on startup (1s interval) | Discover peers |
| `heartbeat` | Master only | Every 5 seconds | Indicate master alive |
| `master_announce` | New master | Once after election | Claim leadership |
| `goodbye` | Exiting node | Once on shutdown | Graceful departure |

**HTTP Sync Endpoints** (not UDP — these are REST API calls):

| Endpoint | Direction | Trigger | Purpose |
|----------|-----------|---------|---------|
| `POST /api/cluster/sync/notify/` | Master → Follower | After each write | Push notification of new sync_log entry |
| `GET /api/cluster/sync/changes/` | Follower → Master | Every 3 seconds (or on notify) | Pull incremental changes |
| `POST /api/cluster/sync/ack/` | Follower → Master | After applying changes | Confirm write received |

### 4.2 Message Reliability

UDP is unreliable; implement these mitigations:

1. **Retransmission**: Each `heartbeat` broadcast sent 2 times with 500ms interval
2. **Sequence Numbers**: Include `seq_num` in heartbeat for ordering
3. **ACK Required**: Important messages (`master_announce`, `goodbye`) require ACK from recipients (with retry)

### 4.3 Node ID Format

```
{hostname}_{random_8_chars}
Example: PC01_a3f2b9c1
```

- Hostname provides human readability
- Random suffix ensures uniqueness even with duplicate hostnames

### 4.4 Bully Election Algorithm

**Rule**: Node with highest ID becomes master.

**Process**:

1. **Startup Discovery** (first 5 seconds):
   - Broadcast `announce` messages
   - Collect peer announcements
   - Build active node list

2. **Election Trigger**:
   - No master detected after discovery phase
   - Master heartbeat timeout (15 seconds = 3 missed heartbeats)
   - Received `goodbye` from master

3. **Election Process**:
   ```
   if no_higher_id_nodes_online:
       become_master()
       broadcast(master_announce)
   else:
       wait_for_higher_id_node(timeout=10s)
       if no_master_announce_received:
           restart_election()
   ```

4. **Master Announcement**:
   - Winning node broadcasts `master_announce`
   - All nodes update their master reference
   - Master starts heartbeat loop

### 4.5 Heartbeat and Failure Detection

```
Master Node:
  - Broadcast heartbeat every 5 seconds
  - Include current sync_log_id in heartbeat

Follower Node:
  - Update last_heartbeat_time on each heartbeat
  - If 15 seconds pass without heartbeat:
      mark_master_failed()
      trigger_election()
```

**Graceful Shutdown**:
- Master sends `goodbye` broadcast before exiting
- Followers immediately trigger election (no 15s wait)

---

## 5. Data Synchronization

### 5.1 Sync Log Model

```python
class SyncLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    table_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    operation = models.CharField(max_length=10)  # INSERT, UPDATE, DELETE
    data = models.JSONField()
    version = models.BigIntegerField(default=1)  # For conflict resolution
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sync_log'
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['created_at']),
        ]
```

### 5.2 Sync Data Payload Design

The sync data payload must contain **only the concrete database field values** needed for the follower node to replicate the write operation. It must not include API-response-only fields, and all values must be JSON-serializable.

#### 5.2.1 Data Collection (Master Node)

When the master records a write operation for sync, the payload is built from the **Django model instance** using `model_to_dict()`, not from the DRF serializer response:

```python
from django.forms.models import model_to_dict

# In SyncWriteViewSetMeta._wrap_with_sync:
sync_data = model_to_dict(instance)

# model_to_dict skips editable=False fields (auto_now_add, auto_now).
# Preserve created_at for time-consistent replication across nodes.
if hasattr(instance, 'created_at') and instance.created_at:
    sync_data['created_at'] = instance.created_at

sync_tx.record_insert(table_name=table_name, instance=instance, data=sync_data)
```

**Why `model_to_dict` instead of `serializer.data`:**

DRF serializer output includes fields designed for API consumers that are **not** database columns. Passing `serializer.data` as sync payload causes failures on follower nodes:

| Serializer Field Type | Example | Problem on Follower |
|---|---|---|
| `SerializerMethodField` | `tournament_info`, `rule_info`, `fencer_info` | Not a DB column → `TypeError: unexpected keyword argument` |
| `@property` on model | `is_completed`, `is_draw`, `win_rate` | Not a DB column → same error |
| Nested serializer | `elimination_type` (full dict) | DB expects FK ID, not dict |
| `source=...` with dotted path | `elimination_type_code` | Not a DB column name |
| `write_only=True` FK fields | `tournament_id` (source=`tournament`) | Excluded from response → **missing** on follower |

Using `model_to_dict(instance)` yields only the concrete field names and their raw database values, which are exactly what the follower needs.

#### 5.2.2 Data Cleaning (Follower Node)

When the follower applies a sync change, `SyncManager._clean_data()` transforms the payload into valid kwargs for `objects.create()` / `setattr()`:

```python
@staticmethod
def _clean_data(data, model_class):
    skip_fields = {"id", "updated_at", "last_modified_at"}
    cleaned = {}
    for k, v in data.items():
        if k in skip_fields:
            continue
        try:
            field = model_class._meta.get_field(k)
        except Exception:
            continue   # Skip non-model fields (SerializerMethodField, @property, etc.)

        if isinstance(field, ManyToManyField):
            continue   # Must be set after creation

        # ForeignKey: remap "tournament" → "tournament_id" (attname)
        key = field.attname if isinstance(field, ForeignKey) else k
        v = SyncManager._coerce_value(v, field)
        cleaned[key] = v
    return cleaned
```

**Key design decisions:**

| Decision | Rationale |
|---|---|
| Skip keys not on the model | `model_to_dict` and the JSON round-trip guarantee only model fields, but `_clean_data` also safely handles older sync payloads or manual entries that may contain extra keys |
| Remap FK keys to `attname` | `model_to_dict` returns `{"tournament": <uuid>}` (field name), but `create()` expects `tournament_id=<uuid>` (column name). Using `field.attname` converts correctly |
| Skip ManyToMany fields | M2M relations must be set after the record is created, not passed to `create()` |
| Preserve `created_at` | For time-consistent replication: followers should have the same `created_at` as the master, not the time the sync was applied |
| Skip `updated_at` & `last_modified_at` | These use `auto_now=True` and should reflect the follower's apply time |
| Skip `id` | Passed separately to `create(id=...)` |

#### 5.2.3 JSON Serialization Safety

Before recording sync data to the `JSONField` in `sync_log`, all values are recursively sanitized by `_make_json_serializable()` in `SyncTransaction.record()`:

```python
def _make_json_serializable(data):
    if isinstance(data, (datetime, date)):
        return data.isoformat()
    if isinstance(data, UUID):
        return str(data)
    if isinstance(data, Decimal):
        return str(data)
    if isinstance(data, dict):
        return {k: _make_json_serializable(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [_make_json_serializable(item) for item in data]
    return data
```

This converts `date`, `datetime`, `UUID`, and `Decimal` objects to their string representations, preventing `TypeError: Object of type X is not JSON serializable` when Django writes the `JSONField`.

#### 5.2.4 `created_at` Preservation

Django's `auto_now_add=True` on `created_at` causes `pre_save()` to override any explicitly passed value during `create()`. To preserve the master's `created_at` timestamp:

```python
def _apply_insert(self, model_class, change, registry_entry):
    clean_data = self._clean_data(change.data, model_class)

    # Pop created_at — Django's auto_now_add overrides it during create()
    created_at = clean_data.pop('created_at', None)

    model_class.objects.create(id=change.record_id, **clean_data)

    # Restore created_at after creation
    if created_at:
        model_class.objects.filter(id=change.record_id).update(created_at=created_at)
```

This ensures all nodes have identical `created_at` values for replicated records.

#### 5.2.5 Complete Flow Summary

```
Master Node:
  1. View handles POST /api/events/
  2. SyncWriteViewSetMeta wrapper intercepts the response
  3. Loads the created model instance from queryset
  4. sync_data = model_to_dict(instance)     # Only concrete DB fields
  5. Adds created_at if present                # model_to_dict skips it
  6. _make_json_serializable(sync_data)        # date/UUID/Decimal → strings
  7. sync_tx.record_insert(table, instance, sync_data)
  8. SyncTransaction writes to sync_log.JSONField

Follower Node:
  1. SyncWorker pulls change from master
  2. SyncManager._clean_data(change.data, model_class)
     - Skips non-model keys (if any)
     - Remaps FK keys: "tournament" → "tournament_id"
     - Skips ManyToMany fields
     - Coerces values to correct Python types
  3. _apply_insert():
     - Pop created_at from clean_data
     - objects.create(id=record_id, **clean_data)
     - objects.filter(id=record_id).update(created_at=created_at)
```

### 5.3 Sync State Model

Tracks each follower's sync progress and connection URL for push notifications:

```python
class SyncState(models.Model):
    node_id = models.CharField(max_length=100, primary_key=True)
    last_synced_id = models.BigIntegerField(default=0)
    last_sync_time = models.DateTimeField(auto_now=True)
    url = models.CharField(max_length=200, blank=True, null=True)  # e.g. "http://192.168.1.101:8000"
    
    class Meta:
        db_table = 'sync_state'
```

The `url` field stores each follower's HTTP endpoint, enabling the master to push
notifications via `POST /api/cluster/sync/notify/` when new changes are written.
Follower URLs are registered when nodes announce themselves via
`POST /api/cluster/status/announce/` or discovered via UDP broadcast.

### 5.4 Write Operation Flow (Push Notification + Synchronous Replication)

The system uses a **dual push-pull** approach:
- **Push**: Master notifies followers immediately after each write via HTTP POST
- **Pull**: Followers pull incremental changes from master (triggered by push or periodic)
- **ACK**: Followers confirm replication by sending ACK back to master

```
┌─────────┐     ┌──────────────┐     ┌────────────┐     ┌──────────────┐
│ Client  │     │ Master Node  │     │ SyncLog    │     │ Followers    │
└────┬────┘     └──────┬───────┘     └─────┬──────┘     └──────┬───────┘
     │                 │                   │                   │
     │ POST /api/scores│                   │                   │
     │────────────────>│                   │                   │
     │                 │                   │                   │
     │                 │ BEGIN TRANSACTION │                   │
     │                 │──────────────────>│                   │
     │                 │                   │                   │
     │                 │ INSERT score      │                   │
     │                 │ INSERT sync_log   │                   │
     │                 │<──────────────────│                   │
     │                 │ COMMIT            │                   │
     │                 │──────────────────>│                   │
     │                 │                   │                   │
     │                 │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ Push notification
     │                 │ POST /sync/notify/ {sync_log_id}   │    (fire-and-forget)
     │                 │─────────────────────────────────────>│
     │                 │                   │                   │
     │                 │                   │   Follower SyncWorker triggers
     │                 │                   │   immediate pull:│
     │                 │                   │                   │
     │                 │<────── GET /sync/changes/?since=X ───│─ ─ Pull changes
     │                 │──────────────────>│                   │
     │                 │                   │                   │
     │                 │                   │   Apply change    │
     │                 │                   │   (local SQLite)  │
     │                 │                   │<──────────────────│
     │                 │                   │                   │
     │                 │                   │   Update local    │
     │                 │                   │   DjangoSyncState │
     │                 │                   │<──────────────────│
     │                 │                   │                   │
     │                 │<────── POST /sync/ack/ ──────────────│─ ─ Send ACK
     │                 │                   │                   │
     │     200 OK      │                   │                   │
     │<────────────────│                   │                   │
     │  (or 202 if     │                   │                   │
     │   ACK timeout)  │                   │                   │
```

**Key points:**
1. The push notification (`/sync/notify/`) is **fire-and-forget** — the master does NOT wait for it to complete
2. The master waits for ACKs using `threading.Event` (not asyncio), which is thread-safe for cross-request signaling
3. If no followers acknowledge within the timeout, the master returns `202 Accepted` (write persisted, replication pending)
4. The push notification triggers the follower's `SyncWorker` to immediately pull changes, reducing replication lag to sub-second
5. The periodic pull (every 3 seconds) serves as a fallback for missed push notifications

### 5.5 Synchronous Write Configuration

```python
# In SyncWriteMiddleware (Django middleware)
REPLICA_ACK_REQUIRED = 1  # Minimum ACKs required (configurable)
ACK_TIMEOUT = 5000  # milliseconds

def process_response(request, response):
    if not is_master or status_code >= 400 or method not in WRITE_METHODS:
        return response
    
    sync_log_id = getattr(request, '_sync_log_id', None)
    if sync_log_id is None:
        return response
    
    # 1. Notify followers (fire-and-forget in background thread)
    _notify_followers(sync_log_id)
    
    # 2. Wait for ACKs (threading.Event, not asyncio)
    confirmed = _wait_for_acks(sync_log_id)
    
    if confirmed:
        return response
    else:
        return JsonResponse({
            'detail': 'Write accepted but replication pending',
            'sync_log_id': sync_log_id,
            'confirmed': False,
        }, status=202)

def _notify_followers(sync_log_id):
    """Send push notification to all known followers in background."""
    sync_log = SyncLog.objects.get(id=sync_log_id)
    follower_urls = SyncState.objects.exclude(url__isnull=True).exclude(url='')
    
    proxy = get_follower_proxy()
    thread = threading.Thread(
        target=proxy.broadcast_sync,
        args=(list(follower_urls), sync_log_id, sync_log.table_name, sync_log.record_id),
        daemon=True,
    )
    thread.start()

def _wait_for_acks(sync_log_id):
    """Wait for followers to acknowledge write, using threading.Event."""
    if REPLICA_ACK_REQUIRED <= 0:
        return True
    
    event = sync_manager.ack_queue.register(sync_log_id, REPLICA_ACK_REQUIRED)
    confirmed = event.wait(timeout=ACK_TIMEOUT / 1000.0)
    
    if confirmed:
        return True
    
    return sync_manager.ack_queue.is_confirmed(sync_log_id)
```

### 5.6 Backend SyncWorker (Follower Background Thread)

Each follower node runs a **SyncWorker** background thread that continuously pulls
changes from the master. This ensures data replication occurs even without a frontend
connected.

```python
class SyncWorker:
    """Background sync thread running on every follower node."""
    
    def __init__(self):
        self._thread: Optional[Thread] = None
        self._stop_event = threading.Event()
        self._sync_event = threading.Event()  # For immediate sync trigger
        self._sync_interval = 3.0  # seconds
        self._running = False
    
    def start(self):
        """Start if this node is a cluster follower."""
        config = DjangoClusterConfig.get_config()
        if config.mode != 'cluster' or config.is_master:
            return
        self._running = True
        self._thread = Thread(target=self._sync_loop, daemon=True, name='sync-worker')
        self._thread.start()
    
    def stop(self):
        """Stop the background sync thread."""
        self._stop_event.set()
        self._sync_event.set()  # Wake up thread
        if self._thread:
            self._thread.join(timeout=10)
        self._running = False
    
    def trigger_immediate_sync(self):
        """Called by /notify/ endpoint to trigger immediate pull."""
        self._sync_event.set()
    
    def _sync_loop(self):
        """Main loop: pull changes from master, apply, ACK."""
        while not self._stop_event.is_set():
            try:
                self._do_sync_cycle()
            except Exception as e:
                logger.error(f"Sync cycle error: {e}")
            
            # Wait for next cycle or immediate trigger from /notify/
            self._sync_event.wait(timeout=self._sync_interval)
            self._sync_event.clear()
    
    def _do_sync_cycle(self):
        """One iteration of the sync loop."""
        config = DjangoClusterConfig.get_config()
        if config.mode != 'cluster' or config.is_master or not config.master_url:
            return
        
        master_url = config.master_url
        node_id = config.node_id
        self._sync_interval = config.sync_interval
        
        # Get last applied sync ID from local DjangoSyncState
        sync_state = sync_manager.get_sync_state(node_id)
        last_synced_id = sync_state.last_synced_id if sync_state else 0
        
        # First-time: full sync
        if last_synced_id == 0:
            self._do_full_sync(master_url, node_id)
            return
        
        # Pull incremental changes from master
        response = requests.get(
            f"{master_url}/api/cluster/sync/changes/",
            params={"since": last_synced_id, "limit": 100},
            timeout=10,
        )
        
        if response.status_code != 200:
            logger.error(f"Sync pull failed: HTTP {response.status_code}")
            return
        
        data = response.json()
        changes = data.get("changes", [])
        last_id = data.get("last_id", last_synced_id)
        has_more = data.get("has_more", False)
        
        if not changes:
            return
        
        # Apply changes locally (direct SyncManager call, no HTTP roundtrip)
        sync_changes = [SyncChange(**c) for c in changes]
        results = sync_manager.apply_changes_batch(sync_changes)
        
        # Update local DjangoSyncState
        sync_manager.update_sync_state(node_id, last_id)
        
        # ACK to master
        requests.post(
            f"{master_url}/api/cluster/sync/ack/",
            json={"node_id": node_id, "sync_id": last_id},
            timeout=5,
        )
        
        # If more changes available, trigger immediate next cycle
        if has_more:
            self._sync_event.set()
    
    def _do_full_sync(self, master_url, node_id):
        """Initial full sync when node has no sync state (last_synced_id == 0)."""
        response = requests.get(
            f"{master_url}/api/cluster/sync/full/",
            params={"page": 1, "page_size": 1000},
            timeout=30,
        )
        
        if response.status_code != 200:
            logger.error(f"Full sync failed: HTTP {response.status_code}")
            return
        
        data = response.json()
        latest_sync_id = data.get("latest_sync_id", 0)
        
        for table_name, records in data.get("data", {}).items():
            if table_name not in sync_manager._model_registry:
                continue
            model_class = sync_manager._model_registry[table_name].model_class
            for record in records:
                model_class.objects.update_or_create(id=record["id"], defaults=record)
        
        sync_manager.update_sync_state(node_id, latest_sync_id)
        
        # ACK full sync to master
        requests.post(
            f"{master_url}/api/cluster/sync/ack/",
            json={"node_id": node_id, "sync_id": latest_sync_id},
            timeout=5,
        )
```

**Key design decisions:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Thread type | `threading.Thread(daemon=True)` | Simple, no event loop needed; Django ORM is thread-safe for reads |
| Trigger mechanism | `threading.Event` | Push notification sets the event, waking the worker immediately |
| Sync method | Direct `SyncManager` calls (no local HTTP) | Avoids network roundtrip to self; uses Django ORM directly |
| ACK method | HTTP POST to master | Must go to master so ACK queue is updated for synchronous write confirmation |
| Local sync state | `sync_manager.update_sync_state()` called locally | Fixes `lastSyncTime=null` on followers; creates/updates `DjangoSyncState` in local DB |
| Config source | `DjangoClusterConfig.get_config()` per cycle | Supports runtime config changes (mode, master_url, sync_interval) without restart |
| SQLite concurrency | Acceptable for single-writer | Only SyncWorker writes follower data; master is the single writer for sync_log |

**Startup behavior:**
- `SyncWorker.start()` is called from `ClusterConfig.ready()` (Django app startup)
- Only starts if `mode == "cluster" and is_master == False`
- Skips during `manage.py migrate` or other management commands
- If the node is promoted to master (e.g., after election), the worker stops itself on the next cycle

**Push notification endpoint (`POST /api/cluster/sync/notify/`):**

When the master's `SyncWriteMiddleware.notify_followers()` sends a push notification:

```python
# On the follower's Django server
@action(detail=False, methods=["post"], url_path="notify")
def notify_sync(self, request):
    """
    Receive push notification from master about new sync_log entry.
    Triggers immediate sync on this follower's SyncWorker.
    Returns 200 immediately (non-blocking).
    """
    config = DjangoClusterConfig.get_config()
    if config.is_master:
        return Response({"status": "ignored", "reason": "master_node"})
    
    from backend.apps.cluster.services.sync_worker import sync_worker
    sync_worker.trigger_immediate_sync()
    
    return Response({"status": "notified"})
```

### 5.7 Incremental Sync Protocol

**Note**: Incremental sync is driven by the **backend SyncWorker** on each follower node, not by the frontend. The frontend retains a secondary polling loop for UI status updates, but data replication is entirely backend-driven.

**Request** (Follower SyncWorker → Master):
```
GET /api/cluster/sync/changes/?since={last_applied_id}&limit=100
```

**Response**:
```json
{
  "last_id": 12345,
  "has_more": false,
  "changes": [
    {
      "id": 12340,
      "table_name": "scores",
      "record_id": "score_001",
      "operation": "INSERT",
      "data": {"group_id": "G01", "athlete_id": "A01", "score": 9.5},
      "version": 1,
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

**Follower Apply Logic**:
```python
def apply_change(change):
    model = get_model(change.table_name)

    # _clean_data: strip non-model fields, remap FK keys, coerce types
    clean_data = _clean_data(change.data, model)

    if change.operation == 'INSERT':
        created_at = clean_data.pop('created_at', None)
        model.objects.create(id=change.record_id, **clean_data)
        if created_at:
            model.objects.filter(id=change.record_id).update(created_at=created_at)
    elif change.operation == 'UPDATE':
        # Resolve conflicts using version
        if existing and existing.version > change.version:
            skip_change()
            return
        for key, value in clean_data.items():
            setattr(existing, key, value)
        existing.save(update_fields=list(clean_data.keys()) + ['version'])
    elif change.operation == 'DELETE':
        model.objects.filter(id=change.record_id).delete()
```

### 5.8 Full Sync

**Triggers**:
- `last_synced_id == 0` (new follower with no sync state) — automatic via SyncWorker
- Incremental sync fails (data inconsistency) — SyncWorker falls back to full sync
- Manual trigger via admin panel or API

**Process** (performed by SyncWorker automatically on first join):
```
1. SyncWorker: GET /api/cluster/sync/full/?page=1&page_size=1000
2. Master: Export all data (paginated) with serializers
3. SyncWorker: Apply each record via model_class.objects.update_or_create()
4. SyncWorker: Update local sync_state.last_synced_id = latest_sync_id
5. SyncWorker: POST /api/cluster/sync/ack/ {node_id, sync_id}
```

---

## 6. Network Partition and Conflict Resolution

### 6.1 Partition Scenario

```
Before:  [Master A] <---> [Follower B] <---> [Follower C]

Split:   [Master A]                [Follower B] <---> [Follower C]
         (isolated)                (B becomes new master)

Merge:   Two masters exist with divergent data
```

### 6.2 Conflict Resolution Strategy

**Version Vector** is included with each record:

```python
class VersionedModel(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    version = models.BigIntegerField(default=1)
    last_modified_node = models.CharField(max_length=100)  # Node ID
    last_modified_at = models.DateTimeField(auto_now=True)
    
    def get_vector_clock(self):
        return {
            'node_id': self.last_modified_node,
            'version': self.version,
            'timestamp': self.last_modified_at
        }
```

**Resolution Rules**:

1. **Last-Write-Wins (LWW)**: Records with higher `version` win
2. **Tie-Breaker**: Higher `last_modified_at` timestamp wins
3. **Manual Review Queue**: Critical data (scores) flagged for human review

```python
def resolve_conflict(local_record, remote_record):
    if remote_record.version > local_record.version:
        return remote_record
    elif remote_record.version < local_record.version:
        return local_record
    else:
        # Same version, use timestamp
        if remote_record.last_modified_at > local_record.last_modified_at:
            return remote_record
        return local_record

def needs_manual_review(record_type):
    # Critical records require human verification
    return record_type in ['Score', 'Ranking', 'Elimination']
```

### 6.3 Partition Recovery Process

```
1. Network partition detected (heartbeat restored)
2. Each node announces its vector clock summary
3. If conflicting masters exist:
   a. Node with lower ID steps down as follower
   b. Merge process begins
4. Sync logs are exchanged
5. Conflicts resolved using version vectors
6. Records needing review added to manual_review_queue
7. Admin notified to review conflicts
```

---

## 7. API Routing Strategy

### 7.1 Master Node

| Method | Path | Behavior |
|--------|------|----------|
| GET | /api/* | Serve from local SQLite |
| POST/PUT/DELETE | /api/* | Write to local + sync_log, wait for ACKs |
| GET | /api/sync/changes | Return incremental changes |
| POST | /api/sync/full | Return full data export |
| GET | /api/cluster/status | Return cluster status |

### 7.2 Follower Node

| Method | Path | Behavior |
|--------|------|----------|
| GET | /api/* | Serve from local SQLite |
| POST/PUT/DELETE | /api/* | Return 503 or proxy to master |
| GET | /api/cluster/sync/changes/ | Proxy: pull changes from master |
| POST | /api/cluster/sync/apply/ | Apply received changes to local DB, update local SyncState |
| POST | /api/cluster/sync/notify/ | Receive push notification, trigger immediate SyncWorker cycle |
| GET | /api/cluster/status/ | Return local cluster status and sync lag |

**Push Notification Flow**:
```python
# On master - after writing to sync_log:
notify_followers(sync_log_id)
# → POST http://follower:8000/api/cluster/sync/notify/ {sync_log_id, table_name, record_id}
# → Fire-and-forget in background thread
# → Triggers follower's SyncWorker.trigger_immediate_sync()
```

**Proxy Option** (configurable):
```python
# Follower can proxy writes to master
if settings.PROXY_WRITES_TO_MASTER:
    return proxy_to_master(request, master_url)
else:
    return Response({'error': 'Read-only follower'}, status=503)
```

### 7.3 Frontend Integration

The frontend is **not responsible for data replication**. The backend `SyncWorker` handles all pull-sync and applies changes to the local SQLite database. The frontend's role is:

1. **Read from local backend**: All API calls go to the local Django instance
2. **Write proxy**: If this node is a follower, writes are proxied to the master by `ApiRouterMiddleware`
3. **UI status display**: `ClusterService` polls `/api/cluster/status/` for sync lag, peer status
4. **Full sync trigger**: Manual "Full Sync" button in `ClusterStatus.vue` calls `POST /api/cluster/sync/full/`
5. **Conflict resolution UI**: `ConflictReview.vue` for manual resolution of critical conflicts

```typescript
// Frontend reads from local backend (which SyncWorker keeps up-to-date)
const apiClient = axios.create({
  baseURL: window.location.origin,  // Local Django
});

// For writes on follower, middleware proxies to master automatically
// Frontend uses syncStore for status display only
const syncStore = useSyncStore();
await syncStore.refreshStatus();  // GET /api/cluster/status/
// syncLag, lastSyncTime, isMaster — all from local backend
```

---

## 8. Frontend IndexedDB Strategy

### 8.1 Write-Through Cache with Retry Queue

```
User Action:
1. Write to IndexedDB (status: 'pending')
2. Send HTTP request to master
3. On success: Update IndexedDB (status: 'synced')
4. On failure:
   - Keep 'pending' status
   - Add to SyncQueue
   - Retry on network recovery
```

### 8.2 Offline-First Read Strategy

```typescript
async function getData(key) {
  // 1. Try IndexedDB first
  const cached = await IndexedDBService.get(key);
  if (cached && isFresh(cached)) {
    return cached;
  }
  
  // 2. Fallback to network
  try {
    const networkData = await apiClient.get(key);
    await IndexedDBService.save(key, networkData);
    return networkData;
  } catch (error) {
    // 3. Return stale cache if network unavailable
    if (cached) {
      return cached;
    }
    throw error;
  }
}
```

### 8.3 Sync Queue Service

```typescript
interface PendingOperation {
  id: string;
  operation: 'INSERT' | 'UPDATE' | 'DELETE';
  table: string;
  data: any;
  retries: number;
  lastAttempt: Date;
}

class SyncQueueService {
  private queue: PendingOperation[] = [];
  private maxRetries = 5;
  
  async addPending(op: PendingOperation): Promise<void> {
    await IndexedDBService.addToSyncQueue(op);
  }
  
  async processQueue(): Promise<void> {
    const pending = await IndexedDBService.getPendingOperations();
    for (const op of pending) {
      try {
        await this.executeOperation(op);
        await IndexedDBService.removeFromQueue(op.id);
      } catch (error) {
        op.retries++;
        if (op.retries >= this.maxRetries) {
          await this.flagForManualReview(op);
        }
      }
    }
  }
  
  private async executeOperation(op: PendingOperation): Promise<void> {
    const masterUrl = await ClusterService.getMasterUrl();
    switch (op.operation) {
      case 'INSERT':
        await axios.post(`${masterUrl}/api/${op.table}`, op.data);
        break;
      case 'UPDATE':
        await axios.put(`${masterUrl}/api/${op.table}/${op.data.id}`, op.data);
        break;
      case 'DELETE':
        await axios.delete(`${masterUrl}/api/${op.table}/${op.data.id}`);
        break;
    }
  }
}
```

---

## 9. Failover and Recovery

### 9.1 Master Failure Detection

```python
class HeartbeatMonitor:
    HEARTBEAT_TIMEOUT = 15  # seconds (3 heartbeats)
    
    def __init__(self):
        self.last_heartbeat = time.time()
        self.master_id = None
        
    def on_heartbeat(self, message):
        if message['type'] == 'heartbeat':
            self.last_heartbeat = time.time()
            self.master_id = message['node_id']
            
    def check_timeout(self):
        if time.time() - self.last_heartbeat > HEARTBEAT_TIMEOUT:
            self.trigger_election()
```

### 9.2 Election Process

```
Timeline of Failover:

T+0s:   Master fails (stops sending heartbeats)
T+15s:  Follower detects timeout (3 missed heartbeats)
T+15s:  Election triggered
T+15s:  Each follower checks if it has highest ID
T+16s:  Highest ID node broadcasts master_announce
T+17s:  New master starts heartbeat
T+20s:  First heartbeat received by all nodes
T+23s:  Normal operation resumes

Total downtime: ~8 seconds
```

### 9.3 Data Recovery After Failover

**Scenario**: Master A crashes with uncommitted data

```
Potential Data Loss:
- Write received by Master A
- Master A wrote to local SQLite + sync_log
- Master A crashed before replica ACK
- Data exists in Master A but not in followers
```

**Mitigation**:

1. **Synchronous Write**: Wait for at least 1 replica ACK
2. **Recovery merge**: When Master A rejoins, its data is merged:
   ```python
   def merge_recovery(node):
       # Node's sync_log contains records not in cluster
       uncommitted = get_uncommitted_sync_log(node)
       for record in uncommitted:
           # Re-apply to current master
           conflict_resolver.resolve(record)
   ```
3. **Manual Review**: Records conflicting with current data go to review queue

---

## 10. Configuration

### 10.1 Configuration File

```json
{
  "cluster": {
    "mode": "cluster",
    "node_id": null,
    "udp_port": 9000,
    "api_port": 8000,
    "heartbeat_interval": 5,
    "heartbeat_timeout": 15,
    "sync_interval": 3,
    "replica_ack_required": 1,
    "ack_timeout": 5000,
    "master_ip": null
  },
  "database": {
    "path": "./data/pistemaster.db"
  }
}
```

### 10.2 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CLUSTER_MODE` | single or cluster | single |
| `NODE_ID` | Override auto-generated ID | auto |
| `MASTER_IP` | Fixed master IP (skip election) | null |
| `UDP_PORT` | UDP broadcast port | 9000 |
| `API_PORT` | HTTP API port | 8000 |
| `SYNC_INTERVAL` | Follower sync interval (seconds) | 3 |
| `REPLICA_ACK` | Minimum replicas to ACK | 1 |

---

## 11. Performance Optimization

### 11.1 Database Optimization

```sql
-- Index sync_log for fast incremental sync
CREATE INDEX idx_sync_log_id ON sync_log(id);
CREATE INDEX idx_sync_log_created ON sync_log(created_at);

-- Partition by time for large datasets
CREATE TABLE sync_log_2025_01 () INHERITS (sync_log);

-- Periodic cleanup
DELETE FROM sync_log WHERE created_at < datetime('now', '-7 days');
```

### 11.2 Network Optimization

- **Batch Sync**: Return up to 100 changes per request
- **Compression**: Enable gzip for sync responses > 1KB
- **Delta Only**: Only send changed fields for UPDATEs
- **Push Notification**: Master notifies followers immediately via HTTP POST /sync/notify/ (implemented)

### 11.3 Frontend Optimization

- **Debounced Writes**: Batch multiple writes into single sync
- **Background Sync**: Use Service Worker for offline queue
- **IndexedDB Indexes**: Optimize queries for common access patterns

---

## 12. Security Considerations

### 12.1 LAN Isolation

- System designed for LAN use only
- No exposure to public internet
- Firewall rules: Only allow UDP 9000 and HTTP 8000 within subnet

### 12.2 API Authentication

```python
# Simple token auth for cluster nodes
CLUSTER_TOKEN = os.environ.get('CLUSTER_TOKEN', 'default-insecure-token')

@api_view(['POST'])
def sync_endpoint(request):
    token = request.headers.get('X-Cluster-Token')
    if token != CLUSTER_TOKEN:
        return Response({'error': 'Unauthorized'}, status=401)
```

### 12.3 Data Encryption

- SQLite encryption via SQLCipher (optional)
- TLS for HTTP in production (optional, add reverse proxy)

---

## 13. Monitoring and Logging

### 13.1 Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `cluster_master_changes` | Number of master elections | > 0 in 5 min |
| `cluster_heartbeat_lag` | Time since last heartbeat | > 10s |
| `sync_lag` | Follower sync delay | > 30s |
| `pending_acks` | Unresolved write ACKs | > 10 |
| `sync_queue_size` | Offline operations queued | > 100 |

### 13.2 Log Events

```
[INFO] Node PC01_abc12 started in cluster mode
[INFO] Discovered 3 peers: [PC02_xyz34, PC03_qwe56, PC04_rty78]
[INFO] Election started, highest ID: PC04_rty78
[INFO] Master changed: null -> PC04_rty78
[INFO] Synchronized to sync_log_id: 12345
[WARN] Heartbeat timeout, triggering election
[ERROR] Sync failed: Conflict on record score_001
```

### 13.3 Admin Panel

Access via `/admin/cluster`:
- Current node role (Master/Follower)
- Connected peers
- Sync status (last_synced_id, lag)
- Pending ACK queue
- Manual conflict resolution queue

---

## 14. Implementation Tasks Breakdown

### Phase 1: Data Models (Backend)

| Task | Priority | Files |
|------|----------|-------|
| Create SyncLog model | High | `backend/apps/core/models/sync_log.py` |
| Create SyncState model | High | `backend/apps/core/models/sync_state.py` |
| Create VersionedModel mixin | Medium | `core/models/base.py` |
| Add sync_log table migration | High | `backend/apps/core/migrations/` |

### Phase 2: Service Discovery (Backend)

| Task | Priority | Files |
|------|----------|-------|
| Implement UDP broadcast service | High | `backend/apps/cluster/services/udp_broadcast.py` |
| Implement NodeDiscovery class | High | `backend/apps/cluster/services/node_discovery.py` |
| Implement HeartbeatMonitor class | High | `backend/apps/cluster/services/heartbeat.py` |
| Implement BullyElection class | High | `backend/apps/cluster/services/election.py` |
| Define message schemas | High | `backend/apps/cluster/schemas/messages.py` |

### Phase 3: Data Sync (Backend)

| Task | Priority | Files |
|------|----------|-------|
| Implement SyncManager class | High | `backend/apps/cluster/services/sync_manager.py` |
| Implement transaction wrapper | High | `backend/apps/cluster/decorators/transaction.py` |
| Create /api/cluster/sync/changes/ endpoint | High | `backend/apps/cluster/views/sync.py` |
| Create /api/cluster/sync/full/ endpoint | High | `backend/apps/cluster/views/sync.py` |
| Create /api/cluster/sync/apply/ endpoint | High | `backend/apps/cluster/views/sync.py` |
| Create /api/cluster/sync/ack/ endpoint | High | `backend/apps/cluster/views/sync.py` |
| Create /api/cluster/sync/notify/ endpoint | High | `backend/apps/cluster/views/sync.py` |
| Implement AckQueue class (threading.Event) | High | `backend/apps/cluster/services/ack_queue.py` |
| Implement SyncWorker background thread | High | `backend/apps/cluster/services/sync_worker.py` |
| Implement synchronous write handler with notify | High | `backend/apps/cluster/middleware/write_sync.py` |
| Add url field to DjangoSyncState model | High | `backend/apps/cluster/models/sync_state.py` |
| Update local SyncState in apply_changes endpoint | Medium | `backend/apps/cluster/views/sync.py` |
| Auto-start SyncWorker in ClusterConfig.ready() | Medium | `backend/apps/cluster/apps.py` |

### Phase 4: API Routing (Backend)

| Task | Priority | Files |
|------|----------|-------|
| Implement ApiRouter middleware | Medium | `backend/apps/cluster/middleware/api_router.py` |
| Implement write proxy to master | Medium | `backend/apps/cluster/services/proxy.py` |
| Create /api/cluster/status endpoint | Medium | `backend/apps/cluster/views/status.py` |

### Phase 5: Frontend Sync Stack

| Task | Priority | Files |
|------|----------|-------|
| Improve IndexedDBService for offline-first | Medium | `web_frontend/src/services/storage/IndexedDBService.ts` |
| Implement SyncQueueService | Medium | `web_frontend/src/services/sync/SyncQueueService.ts` |
| Implement ConflictResolver | Medium | `web_frontend/src/services/sync/ConflictResolver.ts` |
| Implement NetworkService | Medium | `web_frontend/src/services/network/NetworkService.ts` |
| Implement ClusterService | Medium | `web_frontend/src/services/cluster/ClusterService.ts` |
| Create syncStore (Pinia) | Medium | `web_frontend/src/stores/syncStore.ts` |

### Phase 6: Electron Integration

| Task | Priority | Files |
|------|----------|-------|
| Add cluster config management | Medium | `desktop/src/main/config/cluster.ts` |
| Add cluster status IPC handlers | Medium | `desktop/src/main/ipc/cluster-handlers.ts` |
| Add UDP service to main process | Medium | `desktop/src/main/services/udp.ts` |

### Phase 7: UI Components

| Task | Priority | Files |
|------|----------|-------|
| Create ClusterStatus component | Low | `web_frontend/src/components/cluster/ClusterStatus.vue` |
| Create ConflictReview panel | Low | `web_frontend/src/components/cluster/ConflictReview.vue` |
| Create SyncProgress indicator | Low | `web_frontend/src/components/cluster/SyncProgress.vue` |
| Create Settings page for cluster mode | Medium | `web_frontend/src/views/Settings.vue` |

### Phase 8: Settings Page for Cluster Mode

The Settings page allows administrators and schedulers to configure cluster mode on a per-device basis. This is stored in the Electron app's user data directory and does not require backend restart.

#### 8.1 Access Control

- **Allowed Roles**: Admin (ADMIN) and Scheduler (SCHEDULER)
- **Guest users**: Cannot access cluster settings
- **Route Protection**: `meta.requiresAuth` with role check in router guard

#### 8.2 Settings Stored

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `mode` | string | 'single' | 'single' or 'cluster' |
| `nodeId` | string | auto-generated | Unique node identifier |
| `udpPort` | number | 9000 | UDP broadcast port |
| `apiPort` | number | 8000 | HTTP API port |
| `heartbeatInterval` | number | 5 | Heartbeat interval in seconds |
| `heartbeatTimeout` | number | 15 | Master timeout in seconds |
| `syncInterval` | number | 3 | Follower sync interval in seconds |
| `replicaAckRequired` | number | 1 | Minimum ACKs for write confirmation |
| `ackTimeout` | number | 5000 | ACK timeout in milliseconds |
| `masterIp` | string | null | Fixed master IP (optional) |

#### 8.3 Mode Switching Flow

```
User toggles mode├── Check user permission (isAdmin || isScheduler)
│   ├── DENY: Show error "Permission denied"
│   └── ALLOW: Continue
├── Show confirmation dialog
│   ├── Cancel: Revert toggle
│   └── Confirm:
│       ├── Save config to cluster.json
│       ├── Stop UDP service (if running)
│       ├── Start UDP service (if cluster mode)
│       ├── Refresh cluster status
│       └── Show success toast
```

#### 8.4 Configuration File Location

- **Windows**: `%APPDATA%/PisteMaster/config/cluster.json`
- **macOS**: `~/Library/Application Support/PisteMaster/config/cluster.json`
- **Linux**: `~/.local/share/PisteMaster/config/cluster.json`

#### 8.5 Default Configuration

```json
{
  "mode": "single",
  "nodeId": null,
  "udpPort": 9000,
  "apiPort": 8000,
  "heartbeatInterval": 5,
  "heartbeatTimeout": 15,
  "syncInterval": 3,
  "replicaAckRequired": 1,
  "ackTimeout": 5000,
  "masterIp": null
}
```

#### 8.6 Node ID Generation

Node IDs are automatically generated using the format: `{hostname}_{random_8_chars}`

Example: `PC01_a3f2b9c1`

Users can regenerate the node ID if needed.

### Phase 9: Testing & Documentation

| Task | Priority | Files |
|------|----------|-------|
| Unit tests for election algorithm | Medium | `tests/unit/cluster/test_election.py` |
| Integration tests for sync | Medium | `tests/integration/test_sync.py` |
| End-to-end cluster test | Medium | `tests/e2e/test_cluster.py` |
| Deployment guide | Low | `docs/deployment/cluster-setup.md` |
| Troubleshooting guide | Low | `docs/deployment/troubleshooting.md` |

---

## 15. Future Enhancements

| Enhancement | Description | Priority |
|-------------|-------------|----------|
| WebSocket Push Upgrade | Replace HTTP /notify/ with persistent WebSocket for lower overhead | Medium |
| Read Replicas | Allow followers to serve GET requests locally | Medium |
| Metrics Export | Prometheus-compatible metrics endpoint | Low |
| Dashboard UI | Real-time cluster visualization | Low |
| Multi-Master Sharding | Partition by tournament for horizontal scaling | Low |

---

## Appendix A: Message Protocol Details

### A.1 Announce Message

```json
{
  "type": "announce",
  "node_id": "PC01_a3f2b9c1",
  "ip": "192.168.1.100",
  "port": 8000,
  "timestamp": 1704067200,
  "is_master": false,
  "version": 1,
  "seq_num": 1
}
```

### A.2 Heartbeat Message

```json
{
  "type": "heartbeat",
  "node_id": "PC01_a3f2b9c1",
  "timestamp": 1704067200,
  "seq_num": 42,
  "last_sync_id": 12345
}
```

### A.3 Master Announce Message

```json
{
  "type": "master_announce",
  "node_id": "PC04_rty7890",
  "ip": "192.168.1.103",
  "port": 8000,
  "timestamp": 1704067200,
  "seq_num": 1
}
```

### A.4 Goodbye Message

```json
{
  "type": "goodbye",
  "node_id": "PC01_a3f2b9c1",
  "reason": "shutdown",
  "timestamp": 1704067200
}
```

### A.5 Sync Response

```json
{
  "type": "sync_response",
  "node_id": "PC01_a3f2b9c1",
  "last_id": 12345,
  "has_more": false,
  "changes": [...]
}
```

### A.6 ACK Message

```json
{
  "type": "ack",
  "node_id": "PC02_xyz3456",
  "sync_id": 12340,
  "timestamp": 1704067200
}
```

---

## Appendix B: State Machine Diagrams

### B.1 Node State Machine

```
                    ┌─────────────────────┐
                    │                     │
                    ▼                     │
┌─────────┐    ┌─────────┐    ┌────────┐  │
│ STARTUP │───>│ DISCOVER │───>│ FOLLOWER│──┘
└─────────┘    └─────────┘    └────────┘     │
     │              │               │        │
     │              │ (highest ID)  │(timeout)
     │              ▼               ▼        │
     │         ┌─────────┐    ┌──────────┐   │
     │         │ ELECTING│───>│ CANDIDATE│───┘
     │         └─────────┘    └──────────┘
     │                              │(win)
     │                              ▼
     │                        ┌─────────┐
     └───────────────────────>│ MASTER  │
                              └─────────┘
                                   │
                                   │(step down)
                                   └────────> FOLLOWER
```

### B.2 Write State Machine

```
┌──────────┐     ┌───────────┐     ┌─────────┐
│ RECEIVED │────>│ PROCESSING│────>│ WRITTEN │
└──────────┘     └───────────┘     └────┬────┘
                       │                 │
                       │(error)          │
                       ▼                 ▼
                  ┌─────────┐      ┌───────────┐
                  │ FAILED   │      │ NOTIFY +  │
                  └─────────┘      │ WAIT_ACK  │
                                   └─────┬─────┘
                                         │
                            ┌────────────┼────────────┐
                            ▼            ▼            ▼
                       ┌────────┐  ┌─────────┐  ┌─────────┐
                       │CONFIRMED│  │PARTIAL  │  │ TIMEOUT │
                       └────────┘  └─────────┘  └─────────┘
```

---

## Appendix C: Error Handling

### C.1 Common Error Scenarios

| Scenario | Detection | Resolution |
|----------|-----------|-------------|
| Network partition | Heartbeat timeout | Trigger election |
| Master crash | Missing heartbeat | Wait ACK timeout, return error to client |
| Sync conflict | Version mismatch | Apply LWW or queue for review |
| UDP packet loss | Sequence gap | Retransmit or poll for missing |
| Database lock | SQLite busy error | Retry with exponential backoff |
| Disk full | Write failure | Alert admin, halt sync |
| SyncWorker crash | Thread not alive | Auto-restart on next health check |
| Push notify missed | Follower lag > threshold | Periodic pull (3s) catches up automatically |

### C.2 Error Response Codes

| Code | Meaning | Client Action |
|------|---------|---------------|
| 200 | Success | Proceed |
| 202 | Accepted (sync pending) | Poll for confirmation |
| 409 | Conflict | Resolve conflict locally |
| 503 | Follower (read-only) | Retry on master or wait |
| 504 | ACK timeout | Retry with new master |

---

*Document Version: 1.1*
*Last Updated: 2026-04-08*
*Changes: Updated Sections 2.1, 2.2, 3.3, 4.1, 5.2-5.8, 7.2, 7.3, 11.2, 14, 15 to reflect backend-driven push+pull sync with SyncWorker, push notification via /sync/notify/, threading.Event for ACK queue, SyncState.url field, and Section 5.2 for sync data payload design (model_to_dict, _clean_data, JSON serialization safety, created_at preservation)*