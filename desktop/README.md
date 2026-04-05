# PisteMaster Desktop Application

Electron-based desktop application for PisteMaster fencing tournament management system.

## Prerequisites

- Node.js 20+
- Python 3.11+ (for development mode)
- PyInstaller (for bundling Python backend)

## Development

### First-time Setup (China / Slow GitHub Access)

If you experience timeout downloading Electron, set the mirror environment variable:

**PowerShell:**
```powershell
$env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
npm install
```

**CMD:**
```cmd
set ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
npm install
```

**Bash/Git Bash:**
```bash
ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/" npm install
```

### Development Commands

```bash
# Install dependencies (use ELECTRON_MIRROR if needed)
npm install

# Run in development mode
npm run dev

# Build without packaging (for testing)
npm run build:unpack

# Build Windows installer
npm run build:win
```

## Development Workflow

The desktop app requires **three services** running simultaneously in development mode:

### Architecture Overview

In development, the desktop app:
- Uses the Django backend from `../backend/` (must be running on port 8000)
- Uses the Vue frontend from `../web_frontend/` (must be running on port 3001)
- Electron loads the frontend via `ELECTRON_RENDERER_URL` environment variable
- **Does NOT bundle Python** - connects to running backend instead

### Three-Terminal Setup

**Terminal 1 - Django Backend:**
```bash
cd backend
python manage.py runserver
# Backend runs on http://localhost:8000
```

**Terminal 2 - Vue Frontend:**
```bash
cd web_frontend
npm run dev
# Frontend runs on http://localhost:3001
```

**Terminal 3 - Electron Desktop App:**
```bash
cd desktop
ELECTRON_RENDERER_URL=http://localhost:3001 npm run dev
```

### Why ELECTRON_RENDERER_URL?

The `electron.vite.config.ts` intentionally omits the renderer configuration because the desktop app shares the frontend with the web version (`web_frontend/`). In development, Electron needs to know where to load the frontend from, which is why we set `ELECTRON_RENDERER_URL=http://localhost:3001`.

In production builds, the frontend is pre-built and copied to the Electron app as static files.

### Alternative: Single Command (From Project Root)

From the project root directory, you can use:
```bash
# Start backend + frontend (in one terminal)
npm run dev

# Then in another terminal, start desktop
npm run dev:electron
```

**Note:** The `dev:electron` script currently doesn't set `ELECTRON_RENDERER_URL`, so you still need to either:
1. Set it manually: `ELECTRON_RENDERER_URL=http://localhost:3001 npm run dev:electron`
2. Or update the script in root `package.json` (see below)

### Updating dev:electron Script (Optional)

To avoid setting the environment variable manually, update `package.json` in the `desktop/` directory:

**Linux/macOS:**
```json
"scripts": {
  "dev": "ELECTRON_RENDERER_URL=http://localhost:3001 electron-vite dev"
}
```

**Cross-platform (requires cross-env):**
```bash
npm install --save-dev cross-env
```
```json
"scripts": {
  "dev": "cross-env ELECTRON_RENDERER_URL=http://localhost:3001 electron-vite dev"
}
```

### GPU Warnings (WSL/Linux)

You may see GPU-related warnings like:
```
[ERROR:viz_main_impl.cc(183)] Exiting GPU process due to errors during initialization
```

These are common in WSL/Linux environments and **don't affect functionality**. The app will work correctly despite these warnings.

To suppress them, you can:

**Option 1: Disable hardware acceleration** (add to `src/main/index.ts`):
```typescript
app.whenReady().then(async () => {
  app.disableHardwareAcceleration()  // Add this line
  // ... rest of the code
})
```

**Option 2: Use command-line flags:**
```bash
ELECTRON_RENDERER_URL=http://localhost:3001 npm run dev -- --disable-gpu
```

### Troubleshooting

**Error: `ERR_FILE_NOT_FOUND`**
- **Cause:** `ELECTRON_RENDERER_URL` not set
- **Solution:** Make sure to set the environment variable or update the dev script

**Error: `Failed to connect to localhost:8000`**
- **Cause:** Django backend not running
- **Solution:** Start the backend first (Terminal 1)

**Error: `Failed to connect to localhost:3001`**
- **Cause:** Vue frontend not running
- **Solution:** Start the frontend (Terminal 2)

**Error: `libnss3.so: cannot open shared object file`**
- **Cause:** Missing Electron dependencies on Linux
- **Solution:** Install required libraries:
```bash
# Ubuntu/Debian
sudo apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2
```

## Architecture

- `src/main/` - Electron main process (Node.js environment)
- `src/preload/` - Preload scripts (Context bridge API)
- `web_frontend/` - Vue renderer process (shared with web version)
- `resources/` - App icons and assets
- `build/` - Build configuration files

## How It Works

1. Electron starts and loads the main process (`src/main/index.ts`)
2. Main process spawns Python/Django backend (`src/main/python-server.ts`)
3. Main window loads the Vue frontend
4. Frontend communicates with backend via HTTP on localhost:8000
5. IPC handlers provide native OS integration (file dialogs, etc.)

## Multi-Instance Development (Cluster Testing)

To test distributed cluster mode with multiple Electron instances, each instance needs its own backend, frontend, and database.

### Architecture for Cluster Testing

| Component | Instance 1 (Master) | Instance 2 (Replica) |
|-----------|---------------------|----------------------|
| Django Backend | Port 8000 | Port 8001 |
| Vue Frontend | Port 3001 | Port 3002 |
| Electron userData | `/tmp/pistemaster-node1` | `/tmp/pistemaster-node2` |
| SQLite Database | `db_node1.sqlite3` | `db_node2.sqlite3` |
| UDP Discovery | Port 9000 | Port 9000 (shared) |

### Setup Steps

**1. Create databases for each instance:**
```bash
# From project root
cd backend
DJANGO_DB_PATH=db_node1.sqlite3 python manage.py migrate
DJANGO_DB_PATH=db_node2.sqlite3 python manage.py migrate
```

**2. Start Backend Instances (separate terminals):**
```bash
# Terminal 1 - Backend Node 1
cd backend
DJANGO_DB_PATH=db_node1.sqlite3 python manage.py runserver 8000

# Terminal 2 - Backend Node 2
cd backend
DJANGO_DB_PATH=db_node2.sqlite3 python manage.py runserver 8001
```

**3. Start Frontend Instances (separate terminals):**
```bash
# Terminal 3 - Frontend Node 1
cd web_frontend
VITE_PORT=3001 VITE_API_PROXY_TARGET=http://localhost:8000 npm run dev

# Terminal 4 - Frontend Node 2
cd web_frontend
VITE_PORT=3002 VITE_API_PROXY_TARGET=http://localhost:8001 npm run dev
```

**4. Start Electron Instances (separate terminals):**
```bash
# Terminal 5 - Electron Node 1
cd desktop
PISTEMASTER_USER_DATA_DIR=/tmp/pistemaster-node1 \
  PISTEMASTER_API_PORT=8000 \
  ELECTRON_RENDERER_URL=http://localhost:3001 \
  npm run dev

# Terminal 6 - Electron Node 2
cd desktop
PISTEMASTER_USER_DATA_DIR=/tmp/pistemaster-node2 \
  PISTEMASTER_API_PORT=8001 \
  ELECTRON_RENDERER_URL=http://localhost:3002 \
  npm run dev
```

### Configuration Notes

- Each Electron instance stores its config in its own `PISTEMASTER_USER_DATA_DIR`, including unique `nodeId`
- `PISTEMASTER_API_PORT` tells each instance which backend port to connect to
- Both instances share UDP port 9000 for auto-discovery (via `SO_REUSEADDR`)
- In cluster settings UI, configure Node 1 as Master and Node 2 as Replica

### Cluster Mode Workflow

1. Start both instances following the steps above
2. In Node 1's cluster settings: Set mode to "cluster", mark as Master
3. In Node 2's cluster settings: Set mode to "cluster", set Master IP to Node 1's IP
4. Nodes will discover each other via UDP broadcast and sync data

## Building

The build process:

1. Compile TypeScript main/preload scripts
2. Build Vue frontend
3. Copy bundled Python backend
4. Package everything with electron-builder
5. Create Windows installer (NSIS)

## Requirements

- Node.js 20+
- Python 3.11+ (for development)
- PyInstaller (for bundling Python backend)