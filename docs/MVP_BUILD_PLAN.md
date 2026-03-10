# PisteMaster MVP Build & Deployment Plan

**Version:** 1.0  
**Updated:** 2026-03-10  
**Scope:** Individual Events Only (Team events post-MVP)

---

## Overview

This document outlines the Minimum Viable Product (MVP) build and deployment plan for PisteMaster, focusing on individual fencing events. The MVP will be deployed in two forms:

1. **Web Version** - Docker deployment on WSL with PostgreSQL
2. **Desktop Version** - Electron app for Windows with embedded backend

---

## Current Implementation Status

### Already Complete (Core MVP)

| Feature | Status | Location |
|---------|--------|----------|
| Tournament CRUD | Complete | Backend + Frontend |
| Event Management | Complete | Backend + Frontend |
| Fencer Import (Manual + Excel paste) | Complete | Frontend |
| Pool Generation & Scoring | Complete | Frontend |
| DE Bracket Visualization | Complete | Frontend |
| Final Ranking Calculation | Complete | Frontend |
| i18n (CN/EN) | Complete | Frontend |
| IndexedDB Schema | Complete | Frontend |

### Incomplete / Placeholders

| Feature | Location | Notes |
|---------|----------|-------|
| Export to Excel | `FinalRanking.vue:132`, `PoolRanking.vue:11` | Shows "开发中" message |
| Print DE Bracket | `DETree.vue:9` | Button exists, no handler |
| Offline Sync | `SyncQueueService.ts` | File is empty |
| Authentication | Backend views | Currently `AllowAny` |

---

## Phase 1: WSL Docker Deployment (PostgreSQL)

### 1.1 Infrastructure Setup

| # | Task | Details | Status |
|---|------|---------|--------|
| 1.1.1 | Create `backend/Dockerfile` | Python 3.12 slim, gunicorn, static files collection | Pending |
| 1.1.2 | Create `web_frontend/Dockerfile` | Node 20, build Vue, nginx serve | Pending |
| 1.1.3 | Create `docker-compose.yml` | postgres + backend + frontend + nginx | Pending |
| 1.1.4 | Create `nginx/nginx.conf` | Reverse proxy `/api` to backend | Pending |
| 1.1.5 | Create `.env.docker` | Environment variables for Docker | Pending |

### 1.2 Backend Configuration

| # | Task | Details | Status |
|---|------|---------|--------|
| 1.2.1 | Add `settings_production.py` | `DEBUG=False`, secure `SECRET_KEY` from env | Pending |
| 1.2.2 | Update `requirements.txt` | Add `psycopg[binary]` for Linux, `gunicorn` | Pending |
| 1.2.3 | Configure PostgreSQL | Database settings from environment variables | Pending |
| 1.2.4 | Add CORS settings | Add WSL IP/domain to `CORS_ALLOWED_ORIGINS` | Pending |
| 1.2.5 | Create entrypoint script | Run migrations + collectstatic on startup | Pending |

### 1.3 Frontend Configuration

| # | Task | Details | Status |
|---|------|---------|--------|
| 1.3.1 | Update `.env.production` | Set `VITE_API_BASE_URL=/api` | Pending |
| 1.3.2 | Configure build output | Static files to `dist/` for nginx | Pending |

### 1.4 Docker Compose Architecture

```yaml
# docker-compose.yml structure
services:
  postgres:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: pistemaster
      POSTGRES_USER: pistemaster
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

  backend:
    build: ./backend
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgres://...
      SECRET_KEY: ${SECRET_KEY}
      DEBUG: "false"

  frontend:
    build: ./web_frontend
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
```

---

## Phase 2: Electron Desktop App (Windows)

### 2.1 Project Setup

| # | Task | Details | Status |
|---|------|---------|--------|
| 2.1.1 | Create `desktop_electron/` directory | New Electron project | Pending |
| 2.1.2 | Initialize `package.json` | Electron, electron-builder dependencies | Pending |
| 2.1.3 | Create `main.js` | Main process, window management | Pending |
| 2.1.4 | Create `preload.js` | Context bridge for IPC | Pending |

### 2.2 Backend Bundling

| # | Task | Details | Status |
|---|------|---------|--------|
| 2.2.1 | Create `backend.spec` | PyInstaller spec for Django backend | Pending |
| 2.2.2 | Bundle Python dependencies | Include all required packages | Pending |
| 2.2.3 | Configure SQLite path | Use user data directory for database | Pending |
| 2.2.4 | Create build script | `npm run build:backend` | Pending |

### 2.3 Electron Integration

| # | Task | Details | Status |
|---|------|---------|--------|
| 2.3.1 | Configure Vue build for Electron | Update `vite.config.ts` | Pending |
| 2.3.2 | Implement backend spawn logic | `child_process.spawn` in `main.js` | Pending |
| 2.3.3 | Handle backend lifecycle | Start on app launch, stop on quit | Pending |
| 2.3.4 | Configure `electron-builder.yml` | Windows installer settings | Pending |
| 2.3.5 | Create build scripts | `npm run build:desktop` | Pending |

### 2.4 Electron Architecture

```
desktop_electron/
├── package.json
├── main.js              # Main process
├── preload.js           # Context bridge
├── electron-builder.yml # Build config
├── resources/
│   └── backend/         # Bundled Python backend
│       └── pistemaster-backend.exe
└── dist/                # Built Vue app
```

```javascript
// main.js structure
const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

let backendProcess = null

function startBackend() {
  const backendPath = path.join(process.resourcesPath, 'backend', 'pistemaster-backend.exe')
  backendProcess = spawn(backendPath, [], { stdio: 'inherit' })
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    }
  })
  win.loadFile('dist/index.html')
}

app.whenReady().then(() => {
  startBackend()
  createWindow()
})

app.on('will-quit', () => {
  if (backendProcess) backendProcess.kill()
})
```

---

## Phase 3: Export & Print Features

### 3.1 Excel Export

| # | Task | Details | Status |
|---|------|---------|--------|
| 3.1.1 | Add xlsx library | `npm install xlsx` in `web_frontend` | Pending |
| 3.1.2 | Implement `exportToExcel()` in `FinalRanking.vue` | Export final ranking table | Pending |
| 3.1.3 | Implement export in `PoolRanking.vue` | Export pool ranking table | Pending |
| 3.1.4 | Implement export in `DETree.vue` | Export bracket data | Pending |

### 3.2 Print Functionality

| # | Task | Details | Status |
|---|------|---------|--------|
| 3.2.1 | Implement print in `DETree.vue` | Use existing `print-js` library | Pending |
| 3.2.2 | Create print styles | CSS `@media print` for clean output | Pending |
| 3.2.3 | Add pool score sheet print | New component for on-piste recording | Pending |

---

## Phase 4: Offline Sync (Post-MVP Enhancement)

| # | Task | Details | Status |
|---|------|---------|--------|
| 4.1 | Implement `SyncQueueService.ts` | Queue offline operations | Pending |
| 4.2 | Add conflict resolution | Handle sync conflicts | Pending |
| 4.3 | Test offline mode E2E | Verify IndexedDB sync | Pending |

---

## Architecture Overview

### Web Version (WSL Docker)

```
┌─────────────────────────────────────────────────────────┐
│  nginx (port 80)                                        │
│    ├── /              → frontend container (static)     │
│    └── /api/*         → backend container (port 8000)  │
│                                                         │
│  postgres container (port 5432)                        │
│    └── volume: ./postgres_data                          │
│                                                         │
│  backend container                                      │
│    └── Django + gunicorn                                │
└─────────────────────────────────────────────────────────┘
```

### Desktop Version (Electron)

```
┌─────────────────────────────────────────────────────────┐
│  Electron main.js                                       │
│    ├── spawns: pistemaster-backend.exe (localhost:8000)│
│    └── loads: Vue app in BrowserWindow                  │
│                                                         │
│  pistemaster-backend.exe                                │
│    └── Django + SQLite (user data directory)           │
└─────────────────────────────────────────────────────────┘
```

---

## Build Commands

### Web Version (Docker)

```bash
# Build and run
docker-compose up --build

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

### Desktop Version (Electron)

```bash
# Build Vue app for Electron
cd web_frontend && npm run build

# Build Python backend
cd desktop_electron && npm run build:backend

# Build Electron app
cd desktop_electron && npm run build:desktop

# Output: PisteMaster-Setup.exe
```

---

## Environment Variables

### Web Version (`.env.docker`)

```env
# PostgreSQL
POSTGRES_DB=pistemaster
POSTGRES_USER=pistemaster
POSTGRES_PASSWORD=<secure_password>

# Django
SECRET_KEY=<secure_secret_key>
DEBUG=false
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost
```

### Desktop Version

```env
# SQLite database path (auto-configured)
DATABASE_PATH=<user_data_directory>/pistemaster/data.db

# Django
SECRET_KEY=<embedded_secret_key>
DEBUG=false
```

---

## Testing Checklist

### Web Version

- [ ] Tournament CRUD operations
- [ ] Event creation and management
- [ ] Fencer import (manual + Excel paste)
- [ ] Pool generation and scoring
- [ ] DE bracket visualization and scoring
- [ ] Final ranking calculation
- [ ] Excel export functionality
- [ ] Print functionality
- [ ] PostgreSQL data persistence

### Desktop Version

- [ ] App launches correctly
- [ ] Backend process starts automatically
- [ ] All web features work offline
- [ ] Database persists between sessions
- [ ] Clean shutdown (backend process killed)
- [ ] Windows installer works

---

## Post-MVP Roadmap

1. **Team Events** - Team brackets, relay matches
2. **Authentication** - JWT-based user system
3. **Piste/Referee Management** - Assignment and scheduling
4. **Live Scoreboard** - WebSocket real-time updates
5. **Distributed Mode** - Multi-client coordination (etcd)
