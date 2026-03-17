# Pistemaster Desktop Application

Electron-based desktop application for PisteMaster fencing tournament management system.

## Development

```bash
# Install dependencies
npm install

# Run in development mode (requires backend running)
npm run dev

# Build without packaging
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