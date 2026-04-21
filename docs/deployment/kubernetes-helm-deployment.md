# PisteMaster Kubernetes + Helm Deployment Guide

This guide covers deploying PisteMaster on Kubernetes using Helm charts for local development/testing on WSL2 with k3s.

## Overview

- **Target Platform**: WSL2 with k3s (Kubernetes)
- **Access URL**: `http://172.23.164.197:30080`
- **Package Manager**: Helm 3

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      k3s Cluster                           │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  postgres   │    │   backend   │    │   frontend  │      │
│  │ (StatefulSet│    │ (Deployment)│    │ (Deployment)│      │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘      │
│         │                  │                  │            │
│    ┌────┴────┐         ┌────┴────┐        ┌───┴────┐        │
│    │ ClusterIP│        │ ClusterIP│       │NodePort│        │
│    │  :5432   │        │  :8000   │       │ :30080 │        │
│    └─────────┘         └─────────┘        └───┬────┘        │
└──────────────────────────────────────────────│────────────┘
                                                  │
                                    Windows Browser ─────────
                                    http://172.23.164.197:30080
```

## Prerequisites

1. **k3s** installed and running on WSL2
2. **Helm 3** installed
3. **Docker** for building images
4. **kubectl** configured to access k3s cluster

### Installing Helm

If Helm is not installed:

```bash
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

Verify installation:

```bash
helm version
```

### Installing k3s

If k3s is not installed:

```bash
curl -sfL https://get.k3s.io | sh -
```

### Fix k3s kubeconfig Permissions

After k3s installation, you may need to fix kubeconfig permissions:

```bash
sudo chmod 644 /etc/rancher/k3s/k3s.yaml
```

### Check k3s Status

```bash
# Verify k3s is running
sudo systemctl status k3s

# Verify kubectl access
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl get nodes
```

## Directory Structure

```
k8s/
├── charts/
│   ├── postgres/           # PostgreSQL StatefulSet + PVC
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   └── templates/
│   │       ├── _helpers.tpl
│   │       ├── StatefulSet.yaml
│   │       ├── Service.yaml
│   │       ├── ConfigMap.yaml
│   │       ├── Secret.yaml
│   │       └── PVC.yaml
│   │
│   ├── backend/            # Django API + Migrations Job
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   └── templates/
│   │       ├── _helpers.tpl
│   │       ├── Deployment.yaml
│   │       ├── Service.yaml
│   │       ├── ConfigMap.yaml
│   │       ├── Secret.yaml
│   │       └── Job.yaml
│   │
│   └── frontend/          # Vue + nginx
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── _helpers.tpl
│           ├── Deployment.yaml
│           ├── Service.yaml
│           └── ConfigMap.yaml
│
└── README.md               # This file
```

## Installation Steps

### 1. Build Docker Images

```bash
# Navigate to project root
cd /home/tian/projects/PisteMaster

# Build backend image
docker build -t pistemaster-backend:latest -f backend/Dockerfile .

# Build frontend image
docker build -t pistemaster-frontend:latest -f web_frontend/Dockerfile .
```

### 2. Import Images into k3s

Since k3s uses containerd directly (not Docker), you need to import images using `ctr`:

```bash
# Save images to tar files
docker save -o /tmp/images/backend.tar pistemaster-backend:latest
docker save -o /tmp/images/frontend.tar pistemaster-frontend:latest
docker save -o /tmp/images/postgres.tar postgres:16-alpine

# Import into k3s containerd
sudo ctr -n k8s.io images import /tmp/images/backend.tar
sudo ctr -n k8s.io images import /tmp/images/frontend.tar
sudo ctr -n k8s.io images import /tmp/images/postgres.tar

# Verify images are loaded
sudo ctr -n k8s.io images list | grep -E "pistemaster|postgres"
```

If using k3d (Docker-based k3s):

```bash
k3d image import pistemaster-backend:latest
k3d image import pistemaster-frontend:latest
```

Alternative: Push to a registry:

```bash
# Tag and push to internal registry (if available)
docker tag pistemaster-backend:latest registry.example.com/pistemaster-backend:latest
docker push registry.example.com/pistemaster-backend:latest
```

### 3. Install Helm Charts

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Create namespace
kubectl create namespace pistemaster

# Install PostgreSQL chart
helm install postgres ./k8s/charts/postgres -n pistemaster

# Wait for postgres to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgres -n pistemaster --timeout=120s

# Install backend chart
helm install backend ./k8s/charts/backend -n pistemaster

# Install frontend chart
helm install frontend ./k8s/charts/frontend -n pistemaster
```

### 4. Run Database Migrations

```bash
# Get backend pod name
BACKEND_POD=$(kubectl get pods -n pistemaster -l app.kubernetes.io/name=backend -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec $BACKEND_POD -n pistemaster -- python manage.py migrate --noinput
```

### 5. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n pistemaster

# Check services
kubectl get svc -n pistemaster

# Check pods logs
kubectl logs -l app.kubernetes.io/name=backend -n pistemaster
```

### 6. Access the Application

Open in Windows browser:

- **Frontend**: http://172.23.164.197:30080
- **Backend API**: http://172.23.164.197:30080/api/
- **Django Admin**: http://172.23.164.197:30080/admin/

## Configuration

### Helm Values

Each chart has its own `values.yaml`. Key settings:

#### PostgreSQL (charts/postgres/values.yaml)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Docker image | `postgres` |
| `image.tag` | Image tag | `16-alpine` |
| `persistence.size` | PVC size | `2Gi` |
| `persistence.storageClass` | Storage class | `local-path` |
| `database` | Database name | `pistemaster` |
| `username` | Database user | `pistemaster` |

**Note**: k3s uses `local-path` storage class (not `standard`).

#### Backend (charts/backend/values.yaml)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Docker image | `pistemaster-backend` |
| `image.tag` | Image tag | `latest` |
| `image.pullPolicy` | Pull policy | `IfNotPresent` |
| `replicaCount` | Number of pods | `1` |
| `service.port` | Service port | `8000` |
| `env.debug` | Django DEBUG mode | `True` |
| `env.allowedHosts` | Allowed hosts | `localhost,127.0.0.1,172.23.164.197` |
| `postgres.host` | PostgreSQL service name | `postgres-postgres` |

#### Frontend (charts/frontend/values.yaml)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Docker image | `pistemaster-frontend` |
| `image.tag` | Image tag | `latest` |
| `image.pullPolicy` | Pull policy | `IfNotPresent` |
| `replicaCount` | Number of pods | `1` |
| `service.type` | Service type | `NodePort` |
| `service.nodePort` | NodePort | `30080` |
| `backendUrl` | Backend API URL | `http://backend-backend:8000` |

## Managing Deployments

### Upgrading

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Upgrade backend with new image
helm upgrade backend ./k8s/charts/backend -n pistemaster --set image.tag=v2

# Upgrade with custom values
helm upgrade backend ./k8s/charts/backend -n pistemaster -f custom-values.yaml
```

### Rollback

```bash
# Rollback backend to previous revision
helm rollback backend -n pistemaster

# Rollback to specific revision
helm rollback backend 2 -n pistemaster
```

### Running Migrations Manually

```bash
# Get backend pod
BACKEND_POD=$(kubectl get pod -l app.kubernetes.io/name=backend -n pistemaster -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec $BACKEND_POD -n pistemaster -- python manage.py migrate --noinput

# Or run shell
kubectl exec -it $BACKEND_POD -n pistemaster -- /bin/sh
```

### Viewing Logs

```bash
# Backend logs
kubectl logs -l app.kubernetes.io/name=backend -n pistemaster -f

# Frontend logs
kubectl logs -l app.kubernetes.io/name=frontend -n pistemaster -f

# Postgres logs
kubectl logs -l app.kubernetes.io/name=postgres -n pistemaster -f
```

## Uninstalling

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Remove all charts
helm uninstall frontend -n pistemaster
helm uninstall backend -n pistemaster
helm uninstall postgres -n pistemaster

# Delete namespace (removes all resources)
kubectl delete namespace pistemaster
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod for details
kubectl describe pod <pod-name> -n pistemaster

# Check events
kubectl get events -n pistemaster --sort-by='.lastTimestamp'
```

### ImagePullBackOff Error

k3s uses containerd, not Docker. Images must be imported using `ctr`:

```bash
# Check if image exists locally
docker images | grep pistemaster

# Import into k3s
sudo ctr -n k8s.io images import /tmp/images/backend.tar
```

### PVC Pending (StorageClass)

k3s uses `local-path` storage class. Check available storage:

```bash
kubectl get storageclass
```

If PVC is stuck, check:
```bash
kubectl describe pvc <pvc-name> -n pistemaster
```

### Database Connection Issues

```bash
# Check postgres pod is running
kubectl get pods -l app.kubernetes.io/name=postgres -n pistemaster

# Test database connection from backend pod
BACKEND_POD=$(kubectl get pod -l app.kubernetes.io/name=backend -n pistemaster -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $BACKEND_POD -n pistemaster -- nc -zv postgres-postgres 5432
```

### PVC Storage Class Mismatch

If you see `spec.storageClassName: standard is not exist`, you need to delete and recreate the PVC:

```bash
# Delete old PVC (this may cause data loss!)
kubectl delete pvc <pvc-name> -n pistemaster

# Helm upgrade will recreate with correct storage class
helm upgrade postgres ./k8s/charts/postgres -n pistemaster
```

### Reset Everything

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Delete namespace and recreate
kubectl delete namespace pistemaster
kubectl create namespace pistemaster

# Re-import images
sudo ctr -n k8s.io images import /tmp/images/backend.tar
sudo ctr -n k8s.io images import /tmp/images/frontend.tar
sudo ctr -n k8s.io images import /tmp/images/postgres.tar

# Fresh install
helm install postgres ./k8s/charts/postgres -n pistemaster
helm install backend ./k8s/charts/backend -n pistemaster
helm install frontend ./k8s/charts/frontend -n pistemaster
```

## Production Considerations

When moving to production:

1. **Secrets Management**: Store `SECRET_KEY` and `POSTGRES_PASSWORD` in Kubernetes Secrets or external secrets manager
2. **TLS**: Install cert-manager for automatic TLS certificates
3. **Ingress**: Replace NodePort with Ingress controller and proper domain names
4. **Storage**: Use persistent volumes with appropriate storage class (consider NFS for multi-node clusters)
5. **Resource Limits**: Add CPU/memory limits and requests
6. **High Availability**: Increase replica counts for backend and frontend
7. **Database**: Consider managed PostgreSQL service for production
8. **Image Registry**: Use a proper image registry instead of importing with `ctr`

## References

- [Helm Documentation](https://helm.sh/docs/)
- [k3s Documentation](https://docs.k3s.io/)
- [k3s Storage](https://docs.k3s.io/storage)
- [Kubernetes StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [Kubernetes Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
