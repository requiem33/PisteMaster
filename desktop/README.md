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

# Run in development mode (requires backend running on port 8000)
npm run dev

# Build without packaging (for testing)
npm run build:unpack

# Build Windows installer
npm run build:win
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