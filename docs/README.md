# PisteMaster Documentation

## Overview

PisteMaster is a professional fencing tournament management system with:
- **Backend**: Django 4.2 + Django REST Framework (Python)
- **Frontend**: Vue 3 + TypeScript + Vite + Element Plus
- **Desktop App**: Electron (Windows) - In Development

## Quick Links

| Document | Description |
|----------|-------------|
| [MVP Build Plan](./MVP_BUILD_PLAN.md) | Current MVP scope and deployment plan |
| [System Architecture](./architecture/PisteMaster-System-Architecture.md) | Overall system design and vision |
| [Database Schema](./domain_models/database_schema.md) | Database design and models |
| [API Design](./api/MVP%20API设计.md) | REST API endpoints |
| [Frontend Architecture](./architecture/MVP%20前端架构设计.md) | Frontend design patterns |

## Current Status

### MVP Scope (Individual Events)

**Completed:**
- Tournament/Event CRUD
- Fencer management with import
- Pool generation & scoring
- DE bracket visualization
- Final ranking calculation
- i18n (CN/EN)

**In Progress:**
- Docker deployment (PostgreSQL)
- Electron desktop app
- Excel export functionality
- Print functionality

**Post-MVP:**
- Team events
- Authentication system
- Piste/Referee management
- Live scoreboard (WebSocket)
- Distributed mode (etcd)

## Development

See [AGENTS.md](../AGENTS.md) for development guidelines and build commands.
