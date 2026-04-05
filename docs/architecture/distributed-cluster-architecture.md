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
┌─────────────────────────────────────────────────────────────────┐
│                      LAN (Gigabit Switch)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Master Node (Electron + Django)                ││
│  │  - Processes all write requests (POST/PUT/DELETE)          ││
│  │  - Writes to local SQLite                                   ││
│  │  - Records change log (sync_log)                           ││
│  │  - Provides incremental sync API                           ││
│  │  - Broadcasts heartbeat via UDP                            ││
│  │  - Waits for replica ACK before responding to client        ││
│  └─────────────────────────────────────────────────────────────┘│
│                              ▲                                  │
│                              │ HTTP Requests (all to master)    │
│                              │ Data Sync (push/pull)            │
│                              │ UDP Broadcast (discovery)        │
│                              ▼                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │ Follower A    │  │ Follower B    │  │ Follower C    │       │
│  │ - Read-only   │  │ - Read-only   │  │ - Read-only   │       │
│  │ - Local SQLite│  │ - Local SQLite│  │ - Local SQLite│       │
│  │ - Pull sync   │  │ - Pull sync   │  │ - Pull sync   │       │
│  │ - ACK writes  │  │ - ACK writes  │  │ - ACK writes  │       │
│  │ - Monitor HB  │  │ - Monitor HB  │  │ - Monitor HB  │       │
│  └───────────────┘  └───────────────┘  └───────────────┘       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │         Service Discovery (UDP Broadcast Port 9000)         ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Core Components

| Component | Responsibility | Location |
|-----------|---------------|----------|
| **NodeDiscovery** | UDP-based node discovery, heartbeat, election | Backend (Python) |
| **HeartbeatMonitor** | Monitor master heartbeat, trigger failover | Backend (Python) |
| **SyncManager** | Change log recording, incremental/full sync | Backend (Python) |
| **SyncLog Model** | Persist change records in SQLite | Backend (Django Model) |
| **ApiRouter** | Route requests based on node role (master/follower) | Backend (Django Middleware) |
| **AckQueue** | Track pending ACKs from followers for synchronous writes | Backend (Python) |
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
| **Master** | Process locally | Process locally | Broadcast heartbeat, record sync_log, wait for ACKs |
| **Follower** | Proxy/Reject (503) | Process locally | Pull sync, ACK writes, monitor heartbeat |

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
| `sync_request` | Follower → Master | Configurable (default 3s) | Request incremental sync |
| `ack` | Follower → Master | After applying sync | Confirm write received |

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

### 5.2 Sync State Model

Tracks each follower's sync progress:

```python
class SyncState(models.Model):
    node_id = models.CharField(max_length=100, primary_key=True)
    last_synced_id = models.BigIntegerField(default=0)
    last_sync_time = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sync_state'
```

### 5.3 Write Operation Flow (Synchronous Replication)

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
     │                 │ Broadcast change via sync endpoint   │
     │                 │─────────────────────────────────────>│
     │                 │                   │                   │
     │                 │                   │   Apply change    │
     │                 │                   │<──────────────────│
     │                 │                   │                   │
     │                 │<────── ACK ──────│───────────────────│
     │                 │                   │                   │
     │     200 OK      │                   │                   │
     │<────────────────│                   │                   │
     │                 │                   │                   │
```

### 5.4 Synchronous Write Configuration

```python
# In write request handler
REPLICA_ACK_REQUIRED = 1  # Minimum ACKs required (configurable)
ACK_TIMEOUT = 5000  # milliseconds

async def handle_write_request(request):
    # 1. Begin transaction
    with transaction.atomic():
        # 2. Execute business logic
        record = perform_write(request)
        
        # 3. Record in sync_log
        sync_log = SyncLog.objects.create(
            table_name=record.table_name,
            record_id=record.id,
            operation='INSERT',
            data=serialize(record),
            version=record.version
        )
        
    # 4. Notify followers
    ack_future = ack_queue.register(sync_log.id, replicas_required=REPLICA_ACK_REQUIRED)
    
    # 5. Broadcast to followers
    broadcast_sync_change(sync_log)
    
    # 6. Wait for ACKs
    try:
        await asyncio.wait_for(ack_future, timeout=ACK_TIMEOUT / 1000)
        return Response({'status': 'confirmed', 'sync_id': sync_log.id})
    except asyncio.TimeoutError:
        return Response({'status': 'partial', 'confirmed_replicas': ack_queue.get_confirmed()},
                        status=503)
```

### 5.5 Incremental Sync Protocol

**Request** (Follower → Master):
```
GET /api/sync/changes?since={last_applied_id}&limit=100
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
    
    if change.operation == 'INSERT':
        model.objects.create(id=change.record_id, **change.data)
    elif change.operation == 'UPDATE':
        model.objects.filter(id=change.record_id).update(**change.data)
    elif change.operation == 'DELETE':
        model.objects.filter(id=change.record_id).delete()
    
    # Resolve conflicts using version
    if existing and existing.version > change.version:
        skip_change()  # Keep newer version
        return
    
    apply_change_with_version(change)
```

### 5.6 Full Sync

**Triggers**:
- New follower joins (no local data)
- Incremental sync fails (data inconsistency)
- Manual trigger via admin panel

**Process**:
```
1. Follower: POST /api/sync/full
2. Master: Export all data (paginated)
   GET /api/sync/full?page=1&tables=tournaments,events,scores
3. Follower: Clear local database
4. Follower: Import all data
5. Follower: Update sync_state.last_synced_id
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
| POST | /api/sync/ack | Acknowledge received change |

**Proxy Option** (configurable):
```python
# Follower can proxy writes to master
if settings.PROXY_WRITES_TO_MASTER:
    return proxy_to_master(request, master_url)
else:
    return Response({'error': 'Read-only follower'}, status=503)
```

### 7.3 Frontend Integration

```typescript
// Frontend discovers master node on startup
const masterUrl = await ClusterService.discoverMaster();

// All API calls go to master
const apiClient = axios.create({
  baseURL: masterUrl,
});

// Handle master switch
ClusterService.onMasterChange((newMasterUrl) => {
  apiClient.defaults.baseURL = newMasterUrl;
});
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
- **WebSocket Option**: Real-time push (future enhancement)

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
| Create /api/sync/changes endpoint | High | `backend/apps/cluster/views/sync.py` |
| Create /api/sync/full endpoint | High | `backend/apps/cluster/views/sync.py` |
| Implement AckQueue class | High | `backend/apps/cluster/services/ack_queue.py` |
| Implement synchronous write handler | High | `backend/apps/cluster/middleware/write_sync.py` |

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
| WebSocket Real-time Push | Replace polling with WebSocket for lower latency | Medium |
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
                 │ FAILED   │      │ BROADCAST │
                 └─────────┘      └─────┬─────┘
                                       │
                                       ▼
                                 ┌───────────┐
                                 │ WAIT_ACK  │
                                 └─────┬─────┘
                                       │
                        ┌──────────────┼──────────────┐
                        ▼              ▼              ▼
                   ┌────────┐    ┌─────────┐   ┌─────────┐
                   │CONFIRMED│    │PARTIAL  │   │ TIMEOUT │
                   └────────┘    └─────────┘   └─────────┘
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

### C.2 Error Response Codes

| Code | Meaning | Client Action |
|------|---------|---------------|
| 200 | Success | Proceed |
| 202 | Accepted (sync pending) | Poll for confirmation |
| 409 | Conflict | Resolve conflict locally |
| 503 | Follower (read-only) | Retry on master or wait |
| 504 | ACK timeout | Retry with new master |

---

*Document Version: 1.0*
*Last Updated: 2025-03-31*