# PisteMaster Documentation

## Overview

PisteMaster is a professional fencing tournament management system with:
- **Backend**: Django 4.2 + Django REST Framework (Python)
- **Frontend**: Vue 3 + TypeScript + Vite + Element Plus
- **Desktop App**: Electron (Windows) - In Development

## Quick Links

### Core Documentation
| Document | Description |
|----------|-------------|
| [MVP Build Plan](./MVP_BUILD_PLAN.md) | Current MVP scope and deployment plan |
| [System Architecture](./architecture/PisteMaster-System-Architecture.md) | Overall system design and vision |
| [Database Schema](./domain_models/database_schema.md) | Database design and models |
| [API Design](./api/MVP%20API设计.md) | REST API endpoints |
| [Development Log](./development_log.md) | Development progress and changes |

### Architecture
| Document | Description |
|----------|-------------|
| [Frontend Architecture](./architecture/前端架构设计.md) | Frontend design patterns |
| [Django Core Architecture](./architecture/Django-Core分层架构开发指南.md) | Backend layered architecture |
| [Distributed Cluster](./architecture/distributed-cluster-architecture.md) | Cluster architecture for multi-client |
| [User System](./architecture/user-system.md) | User management and authentication |

### Development Guides
| Document | Description |
|----------|-------------|
| [Build Guide](./BUILD.md) | Build and deployment instructions |
| [Style Guides](./style_guides.md) | Code style guidelines |
| [Testing Guide](./testing-guide.md) | Testing strategies and coverage |

### Deployment
| Document | Description |
|----------|-------------|
| [Cluster Setup](./deployment/cluster-setup.md) | Cluster deployment configuration |
| [Troubleshooting](./deployment/troubleshooting.md) | Common issues and solutions |

## Current Status

### MVP Scope (Individual Events)

**Completed:**
- Tournament/Event CRUD
- Fencer management with import
- Pool generation & scoring
- DE bracket visualization
- Final ranking calculation
- i18n (CN/EN)
- JWT Authentication system
- Cluster sync with Master/Follower architecture
- Sync logging for all operations (including custom @action endpoints)
- Electron desktop app (Settings, cluster management)

**In Progress:**
- Docker deployment (PostgreSQL)
- Excel export functionality
- Print functionality
- PyInstaller bundling for desktop

**Post-MVP:**
- Team events
- Piste/Referee management
- Live scoreboard (WebSocket)
- Distributed mode (etcd)
- macOS/Linux desktop support

## Development

See [AGENTS.md](../AGENTS.md) for development guidelines and build commands.
