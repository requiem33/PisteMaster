# PisteMaster Kubernetes Helm Charts

This directory contains Helm charts for deploying PisteMaster on Kubernetes/k3s.

## Charts

- [postgres](postgres/) - PostgreSQL database
- [backend](backend/) - Django REST API
- [frontend](frontend/) - Vue.js web application

## Quick Start

```bash
# Create namespace
kubectl create namespace pistemaster

# Install all charts
helm install postgres ./charts/postgres -n pistemaster
helm install backend ./charts/backend -n pistemaster
helm install frontend ./charts/frontend -n pistemaster

# Check status
kubectl get pods -n pistemaster

# Access the application
# http://172.23.164.197:30080
```

## Documentation

See [docs/deployment/kubernetes-helm-deployment.md](../../docs/deployment/kubernetes-helm-deployment.md) for detailed documentation.
