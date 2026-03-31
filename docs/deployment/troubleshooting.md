# PisteMaster Cluster Troubleshooting Guide

This guide covers common issues and solutions for PisteMaster cluster deployments.

## Table of Contents

1. [Node Discovery Issues](#node-discovery-issues)
2. [Leader Election Problems](#leader-election-problems)
3. [Data Synchronization Issues](#data-synchronization-issues)
4. [Network Problems](#network-problems)
5. [Performance Issues](#performance-issues)
6. [Common Error Messages](#common-error-messages)

---

## Node Discovery Issues

### Symptoms
- Nodes cannot find each other
- Cluster shows only one node
- "No peers discovered" in logs

### Diagnosis

```bash
# Check if UDP port is listening
netstat -ulnp | grep 49152

# Check firewall rules
iptables -L -n | grep 49152

# Test UDP connectivity
nc -u -zv <peer-ip> 49152
```

### Solutions

#### 1. Firewall Blocking UDP
```bash
# Allow UDP discovery port
iptables -A INPUT -p udp --dport 49152 -j ACCEPT

# For firewalld
firewall-cmd --add-port=49152/udp --permanent
firewall-cmd --reload
```

#### 2. Wrong Network Interface
If multiple network interfaces, specify the correct one:

```python
# settings.py
CLUSTER_CONFIG = {
    'bind_address': '192.168.1.100',  # Specific interface
    # ...other settings...
}
```

#### 3. Discovery Timeout Too Short
```python
# Increase discovery timeout in settings.py
CLUSTER_CONFIG = {
    'discovery_timeout': 10.0,  # Default: 5.0
    # ...
}
```

#### 4. Docker/Container Networking
When running in containers, use host networking or configure multicast:

```yaml
# docker-compose.yml
services:
  pistemaster:
    network_mode: "host"
```

---

## Leader Election Problems

### Symptoms
- Multiple nodes claim to be master
- Frequent master changes
- "Election loop" in logs
- No master elected

### Diagnosis

```bash
# Check current cluster status
curl http://localhost:8000/api/cluster/status

# Check election state in logs
grep -E "(Election|MASTER|FOLLOWER)" /var/log/pistemaster/app.log
```

### Solutions

#### 1. Multiple Masters (Split Brain)
This occurs when network partition prevents nodes from communicating:

```bash
# On each node, check peer count
curl http://localhost:8000/api/cluster/peers

# Manually step down the minority master
curl -X POST http://minority-master-ip:8000/api/cluster/step-down
```

**Prevention**: Configure proper quorum requirements

```python
# settings.py
CLUSTER_CONFIG = {
    'replica_ack_required': 2,  # Require majority ACK
    # ...
}
```

#### 2. Election Loop
If nodes keep triggering elections:

```python
# Increase election timeout
CLUSTER_CONFIG = {
    'election_timeout': 15.0,  # Default: 10.0
    'heartbeat_interval': 5.0,
    'heartbeat_timeout': 20.0,  # Must be > heartbeat_interval * 3
    # ...
}
```

#### 3. Master Not Announced
Check if master announcement broadcast is working:

```bash
# Monitor UDP traffic
tcpdump -i any udp port 49152 -A

# You should see MASTER_ANNOUNCE messages
```

#### 4. Node ID Conflicts
Ensure each node has a unique ID:

```bash
# Check node IDs in cluster
for ip in 192.168.1.{100,101,102}; do
    echo "Node $ip:"
    curl -s http://$ip:8000/api/cluster/status | jq '.node_id'
done
```

---

## Data Synchronization Issues

### Symptoms
- Data missing on follower nodes
- Inconsistent data across nodes
- Sync errors in logs
- High sync queue depth

### Diagnosis

```bash
# Check sync status
curl http://localhost:8000/api/cluster/sync/status

# Check sync log entries
curl http://localhost:8000/api/cluster/sync/logs?limit=100

# Check for pending ACKs
curl http://localhost:8000/api/cluster/sync/pending
```

### Solutions

#### 1. Sync Lag (Faller Behind)
Follower is not receiving updates fast enough:

```python
# Increase batch size for sync
CLUSTER_CONFIG = {
    'sync_batch_size': 500,  # Default: 100
    # ...
}
```

#### 2. Sync Conflicts
For conflict resolution issues:

```bash
# View conflicts
curl http://localhost:8000/api/cluster/sync/conflicts

# Manually resolve a conflict
curl -X POST http://localhost:8000/api/cluster/sync/conflicts/{id}/resolve \
  -H "Content-Type: application/json" \
  -d '{"resolution": "use_latest"}'
```

#### 3. Database Lock Issues

```sql
-- Check for long-running transactions
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';

-- Kill blocking transaction if needed
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = <pid>;
```

#### 4. ACK Timeout
If master keeps timing out waiting for ACKs:

```python
# Increase ACK timeout
CLUSTER_CONFIG = {
    'ack_timeout_ms': 10000,  # Default: 5000
    'replica_ack_required': 1,  # Lower requirement temporarily
    # ...
}
```

#### 5. Full Sync Required
If incremental sync fails, force full sync:

```bash
# On follower node
curl -X POST http://follower-ip:8000/api/cluster/sync/full

# This will request full data export from master
```

---

## Network Problems

### Symptoms
- Intermittent connection drops
- High latency between nodes
- Packet loss

### Diagnosis

```bash
# Test connectivity between nodes
ping -c 10 <peer-ip>

# Check packet loss
mtr -r -c 100 <peer-ip>

# Monitor network throughput
iftop -i eth0
```

### Solutions

#### 1. High Latency
Adjust timeouts for slow networks:

```python
CLUSTER_CONFIG = {
    'heartbeat_timeout': 30.0,  # Increase for high latency
    'election_timeout': 20.0,
    'ack_timeout_ms': 15000,
    'discovery_timeout': 15.0,
    # ...
}
```

#### 2. Network Partition Recovery
After network partition heals:

```bash
# Check sync state
curl http://localhost:8000/api/cluster/sync/status

# If out of sync, trigger full sync on partitioned node
curl -X POST http://partitioned-node:8000/api/cluster/sync/full
```

#### 3. UDP Broadcast Not Working (WiFi/Switch)
Some network equipment blocks UDP broadcast:

```python
# Use multicast instead
CLUSTER_CONFIG = {
    'use_multicast': True,
    'multicast_group': '239.0.0.1',
    'multicast_port': 49152,
    # ...
}
```

---

## Performance Issues

### Symptoms
- Slow write operations
- High CPU/memory usage
- Database connection pool exhaustion

### Diagnosis

```bash
# Check sync queue depth
curl http://localhost:8000/api/cluster/sync/pending | jq 'length'

# Monitor process memory
ps aux | grep pistemaster

# Database connections
psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='pistemaster';"
```

### Solutions

#### 1. Sync Queue Backlog
If sync queue is growing:

```bash
# Check queue size
curl http://localhost:8000/api/cluster/sync/pending/count

# Increase batch processing
# In settings.py
CLUSTER_CONFIG = {
    'sync_batch_size': 500,
    'sync_interval_ms': 100,  # Process batches more frequently
    # ...
}
```

#### 2. Too Many Database Connections

```python
# settings.py - configure connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 60
DATABASES['default']['OPTIONS'] = {
    'MAX_CONNS': 20,
    'MIN_CONNS': 5,
}
```

#### 3. Heartbeat Storm
If too many heartbeats:

```python
# Reduce heartbeat frequency
CLUSTER_CONFIG = {
    'heartbeat_interval': 10.0,  # Default: 5.0
    # ...
}
```

#### 4. Large Data Sync
For large tournament data:

```bash
# Use pagination
curl "http://localhost:8000/api/cluster/sync/changes?since=0&limit=500"

# Export in chunks
curl "http://localhost:8000/api/cluster/sync/export?tables=tournament,fencer&chunk_size=1000"
```

---

## Common Error Messages

### "Heartbeat timeout from master"
**Cause**: Master node is unreachable or overloaded

**Solution**:
1. Check master node health
2. Check network connectivity
3. Increase heartbeat timeout

### "Election already in progress"
**Cause**: Another election triggered while one is running

**Solution**: This is normal, wait for election to complete

### "Failed to apply sync change"
**Cause**: Data conflict or corruption

**Solution**:
```bash
# Check conflicting record
curl http://localhost:8000/api/cluster/sync/logs/{id}

# Force apply or skip
curl -X POST http://localhost:8000/api/cluster/sync/logs/{id}/skip
```

### "Write accepted but replication pending"
**Cause**: ACK timeout, data written locally but not replicated

**Solution**:
1. Check follower connectivity
2. Verify sync is progressing
3. Increase ACK timeout if network is slow

### "This node is read-only"
**Cause**: Request sent to follower instead of master

**Solution**:
1. Route write requests to master
2. Use API router middleware to proxy to master
3. Check master status: `curl http://localhost:8000/api/cluster/status`

### "Node expired (no heartbeat received)"
**Cause**: Node lost from cluster due to timeout

**Solution**:
1. Check why node failed (logs, resources)
2. Restart the failed node
3. It will automatically rejoin the cluster

---

## Debugging Tools

### Enable Debug Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'backend.apps.cluster': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Inspect UDP Messages

```bash
# Capture all cluster UDP traffic
tcpdump -i any udp port 49152 -s0 -w cluster.pcap

# Read captured packets
tcpdump -r cluster.pcap -A
```

### Database Queries

```sql
-- Check sync log entries
SELECT id, table_name, operation, created_at 
FROM sync_log 
ORDER BY created_at DESC 
LIMIT 20;

-- Check sync state per node
SELECT * FROM sync_state;

-- Check for stuck sync logs
SELECT COUNT(*) FROM sync_log WHERE created_at < now() - interval '1 hour';
```

### Health Check Script

```bash
#!/bin/bash
# cluster-health.sh

for node in node1 node2 node3; do
    echo "Checking $node..."
    curl -s "http://$node:8000/api/cluster/status" | jq '{
        node_id,
        role,
        peer_count: (.peers | length),
        sync_id,
        healthy
    }'
done
```

---

## Getting Help

If you cannot resolve an issue:

1. Collect logs from all nodes
2. Run health check on each node
3. Check database state
4. Open an issue with:
   - Full error messages
   - Cluster configuration
   - Network topology
   - Steps to reproduce

For more information, see the [Cluster Architecture Documentation](../architecture/distributed-cluster-architecture.md).