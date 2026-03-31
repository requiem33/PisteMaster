# PisteMaster Cluster Deployment Guide

This guide covers deploying PisteMaster in a distributed cluster configuration for LAN environments without a central server.

## Architecture Overview

PisteMaster uses a leader-follower pattern with automatic failover:

- **Master Node**: Handles all write operations and replicates to followers
- **Follower Nodes**: Receive replicated data and can handle read operations
- **Automatic Leader Election**: Bully algorithm for master selection
- **UDP Discovery**: Nodes find each other via UDP broadcast on port 49152
- **API Communication**: HTTP/REST on configured port (default 8000)

## Prerequisites

- Python 3.10+
- PostgreSQL 14+ (recommended for production)
- Network connectivity between nodes (same LAN)
- Firewall allowing UDP port 49152 and configured API port

## Configuration

### Environment Variables

Each node requires the following configuration:

```bash
# .env file for each node
DJANGO_SETTINGS_MODULE=PisteMaster.settings

# Cluster Configuration
CLUSTER_MODE=cluster                    # 'single' or 'cluster'
NODE_ID=node_001                        # Unique identifier for this node
CLUSTER_UDP_PORT=49152                  # UDP discovery port
CLUSTER_API_PORT=8000                   # HTTP API port

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgres://user:pass@localhost:5432/pistemaster

# Security
SECRET_KEY=your-secret-key-here
DEBUG=false
ALLOWED_HOSTS=192.168.1.100,localhost
```

### Django Settings

Add to your `settings.py`:

```python
CLUSTER_CONFIG = {
    'mode': os.environ.get('CLUSTER_MODE', 'single'),
    'udp_port': int(os.environ.get('CLUSTER_UDP_PORT', 49152)),
    'api_port': int(os.environ.get('CLUSTER_API_PORT', 8000)),
    'node_id': os.environ.get('NODE_ID'),
    'heartbeat_interval': 5.0,         # seconds
    'heartbeat_timeout': 15.0,          # seconds
    'election_timeout': 10.0,            # seconds
    'node_expiry_timeout': 30.0,         # seconds
    'replica_ack_required': 1,           # minimum ACKs for write confirmation
    'ack_timeout_ms': 5000,              # timeout for ACK wait
}
```

## Deployment Steps

### 1. Prepare Database

```bash
# Create database
createdb pistemaster

# Run migrations
cd backend
python manage.py migrate
```

### 2. Configure First Node (Will Become Master)

```bash
# Clone/copy application to node
cd /opt/pistemaster

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cat > .env <<EOF
CLUSTER_MODE=cluster
NODE_ID=node_001
CLUSTER_UDP_PORT=49152
CLUSTER_API_PORT=8000
DATABASE_URL=postgres://pistemaster:password@localhost:5432/pistemaster
SECRET_KEY=your-secret-key
DEBUG=false
EOF

# Start the application
python manage.py runserver 0.0.0.0:8000
```

### 3. Configure Additional Nodes

For each follower node, use similar configuration with unique `NODE_ID`:

```bash
# Node 2
cat > .env <<EOF
CLUSTER_MODE=cluster
NODE_ID=node_002
CLUSTER_UDP_PORT=49152
CLUSTER_API_PORT=8000
DATABASE_URL=postgres://pistemaster:password@localhost:5432/pistemaster
SECRET_KEY=your-secret-key
DEBUG=false
EOF

python manage.py runserver 0.0.0.0:8000
```

### 4. Verify Cluster Formation

Check logs for cluster formation:

```
[INFO] Starting node discovery...
[INFO] Discovered node node_002 at 192.168.1.101:8000
[INFO] Node node_001 is now MASTER at 192.168.1.100:8000
[INFO] Follower node_002 connected
```

## Network Configuration

### Firewall Rules

Ensure the following ports are open:

| Port | Protocol | Purpose |
|------|----------|---------|
| 8000 | TCP | HTTP API |
| 49152 | UDP | Node Discovery |

### iptables Example

```bash
# Allow UDP discovery
iptables -A INPUT -p udp --dport 49152 -j ACCEPT

# Allow HTTP API
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

### Systemd Service

Create `/etc/systemd/system/pistemaster.service`:

```ini
[Unit]
Description=PisteMaster Fencing Tournament Management
After=network.target postgresql.service

[Service]
Type=simple
User=pistemaster
Group=pistemaster
WorkingDirectory=/opt/pistemaster/backend
Environment="PATH=/opt/pistemaster/venv/bin"
EnvironmentFile=/opt/pistemaster/.env
ExecStart=/opt/pistemaster/venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    PisteMaster.wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
systemctl daemon-reload
systemctl enable pistemaster
systemctl start pistemaster
```

## Cluster Operations

### Starting the Cluster

1. Start the first node - it will become master
2. Wait for master election (check logs)
3. Start additional nodes - they will discover the master and become followers

### Adding a New Node

1. Configure the new node with unique `NODE_ID`
2. Ensure network connectivity to existing cluster
3. Start the node - it will automatically discover peers and join

### Removing a Node

```bash
# Graceful shutdown (node announces departure)
curl -X POST http://node-ip:8000/api/cluster/shutdown

# Or simply stop the service
systemctl stop pistemaster
```

### Manual Master Step-Down

If you need to demote a master node:

```bash
curl -X POST http://master-ip:8000/api/cluster/step-down
```

## Monitoring

### Health Check Endpoints

```bash
# Node status
curl http://node-ip:8000/api/cluster/status

# Response:
{
    "node_id": "node_001",
    "role": "master",
    "peers": ["node_002", "node_003"],
    "sync_id": 12345,
    "healthy": true
}
```

### Sync Status

```bash
# Sync progress
curl http://node-ip:8000/api/cluster/sync/status
```

### Logs

Important log patterns to monitor:

```
[INFO] Node {node_id} is now MASTER
[INFO] Node {node_id} is now FOLLOWER, master is {master_id}
[WARNING] Heartbeat timeout: {seconds}s since last heartbeat
[INFO] Election triggered by node {node_id}
[INFO] Sync log {id} confirmed by {count} node(s)
[WARNING] Node {node_id} expired (no heartbeat received)
```

## Production Recommendations

### Database

- Use PostgreSQL with streaming replication
- Configure connection pooling
- Regular backups

### Load Balancing

For read operations, you can load-balance across followers:

```nginx
upstream pistemaster_read {
    server 192.168.1.101:8000;
    server 192.168.1.102:8000;
    server 192.168.1.103:8000;
}

upstream pistemaster_write {
    server 192.168.1.100:8000;  # Master node
}
```

### Performance Tuning

```python
# settings.py
CLUSTER_CONFIG = {
    # ... other settings ...
    'replica_ack_required': 2,      # Increase for stronger consistency
    'ack_timeout_ms': 5000,          # Adjust based on network latency
    'heartbeat_interval': 5.0,       # More frequent for faster detection
}
```

### Security

- Use HTTPS for API communication
- Configure firewall rules
- Use strong `SECRET_KEY`
- Disable `DEBUG` in production

## Running Tests

```bash
# Unit tests
pytest tests/unit/cluster/

# Integration tests
pytest tests/integration/test_sync.py

# E2E cluster tests
pytest tests/e2e/test_cluster.py

# All tests
pytest tests/
```

## Scaling Considerations

- **3-5 nodes recommended** for balance between availability and complexity
- **Odd number of nodes** preferred for quorum-based decisions
- Write operations bottlenecked at master - scale reads horizontally
- Consider read replicas for heavy read workloads