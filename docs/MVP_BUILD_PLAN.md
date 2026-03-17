# PisteMaster MVP Build & Deployment Plan

**Version:** 2.0  
**Updated:** 2026-03-17  
**Scope:** Desktop Application (Electron) + CI/CD Pipeline

---

## Executive Summary

This document outlines the build and deployment strategy for PisteMaster, focusing on:

1. **Electron Desktop App** - Windows application with embedded Django backend (SQLite)
2. **Web Version** - Docker deployment with PostgreSQL (existing infrastructure)
3. **CI/CD Pipeline** - GitHub Actions for automated builds and releases

### Key Architecture Decision

| Version | Frontend | Backend | Database | Use Case |
|---------|----------|---------|----------|----------|
| **Desktop** | Electron + Vue | Embedded Django (PyInstaller) | SQLite (local file) | Offline tournament venues |
| **Web** | Vue SPA | Django (Docker/WSL) | PostgreSQL (Docker volume) | Multi-user/online scenarios |

---

## Project Structure Changes

### Directory Reorganization

```
PisteMaster/
├── desktop/                      # NEW: Electron desktop application
│   ├── src/
│   │   ├── main/                 # Electron main process
│   │   │   ├── index.ts          # Entry point
│   │   │   ├── app.ts            # App lifecycle
│   │   │   ├── python-server.ts  # Django subprocess management
│   │   │   ├── ipc-handlers.ts   # IPC communication
│   │   │   └── window-state.ts   # Window persistence
│   │   └── preload/
│   │       └── index.ts           # Context bridge API
│   ├── resources/
│   │   ├── icons/                # App icons (ico, icns, png)
│   │   └── python/               # Bundled Python runtime
│   ├── build/                    # electron-builder config
│   │   └── installer.nsh         # Custom NSIS installer options
│   ├── package.json
│   ├── electron.vite.config.ts
│   └── tsconfig.json
│
├── web_frontend/                 # EXISTING: Vue web application (shared)
│   └── src/                      # Frontend source (used by both versions)
│
├── backend/                      # EXISTING: Django backend
│   ├── PisteMaster/
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Common settings
│   │   │   ├── development.py    # SQLite (current default)
│   │   │   ├── production.py     # PostgreSQL for web
│   │   │   └── desktop.py        # SQLite for Electron
│   │   └── settings.py           # Entry point (loads based on env)
│   └── PisteMaster.spec          # NEW: PyInstaller spec file
│
├── core/                         # EXISTING: Shared domain models
│
├── .github/
│   └── workflows/
│       ├── build-desktop.yml     # Electron build workflow
│       ├── build-web.yml         # Docker build workflow
│       └── release.yml           # Release automation
│
├── scripts/                      # NEW: Build and utility scripts
│   ├── build-python.sh            # PyInstaller build script
│   ├── build-python.ps1           # Windows version
│   └── dev-electron.sh            # Run Electron in dev mode
│
├── docker-compose.yml            # NEW: For web version
├── .env.docker                   # NEW: Docker environment variables
└── package.json                  # Root package.json (build scripts)
```

### Files to Delete

```
desktop_app/                       # OLD: Will be replaced by desktop/
```

---

## Current Implementation Status

### Already Complete (Core MVP)

| Feature | Status | Location |
|---------|--------|----------|
| Tournament CRUD | Complete | `backend/` + `web_frontend/src/views/` |
| Event Management | Complete | `backend/` + `web_frontend/src/views/EventOrchestrator.vue` |
| Fencer Import (Manual + Excel paste) | Complete | `web_frontend/src/components/tournament/FencerImport.vue` |
| Pool Generation & Scoring | Complete | `web_frontend/src/components/tournament/Pool*` |
| DE Bracket Visualization | Complete | `web_frontend/src/components/tournament/DETree.vue` |
| Final Ranking Calculation | Complete | `web_frontend/src/components/tournament/FinalRanking.vue` |
| i18n (CN/EN) | Complete | `web_frontend/src/locales/` |
| IndexedDB Schema | Complete | `web_frontend/src/services/` |

### Complete Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Core MVP Features | 95% | Minor polish needed |
| Electron Infrastructure | 0% | This document |
| CI/CD Pipeline | 0% | This document |
| PyInstaller Bundling | 0% | This document |

---

## Phase 1: Database Configuration (Multi-Environment)

### 1.1 Settings Refactor

Split Django settings into multiple files for different environments:

| # | Task | Details | Status |
|---|------|---------|--------|
| 1.1.1 | Create `settings/base.py` | Common settings (INSTALLED_APPS, MIDDLEWARE, etc.) | Pending |
| 1.1.2 | Create `settings/development.py` | SQLite, DEBUG=True | Pending |
| 1.1.3 | Create `settings/production.py` | PostgreSQL from env, DEBUG=False | Pending |
| 1.1.4 | Create `settings/desktop.py` | SQLite in user data dir, DEBUG=False | Pending |
| 1.1.5 | Update `settings.py` | Load correct settings based on `DJANGO_SETTINGS_MODULE` | Pending |

### 1.2 Settings Architecture

```python
# settings/base.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TRUE_BASE_DIR = BASE_DIR.parent

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    # ... rest of apps
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    # ... rest of middleware
]

# ... common settings

# settings/development.py
from .base import *

DEBUG = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# settings/production.py
import os
from .base import *

DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "pistemaster"),
        "USER": os.environ.get("POSTGRES_USER", "pistemaster"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "postgres"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# settings/desktop.py
import os
from pathlib import Path
from .base import *

DEBUG = False

def get_desktop_db_path():
    """Get platform-specific user data directory for SQLite database."""
    app_name = "PisteMaster"
    if os.name == 'nt':  # Windows
        base = Path(os.environ.get('APPDATA', Path.home()))
    elif os.name == 'darwin':  # macOS
        base = Path.home() / 'Library' / 'Application Support'
    else:  # Linux
        base = Path.home() / '.local' / 'share'
    
    data_dir = base / app_name / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / 'pistemaster.db'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": get_desktop_db_path(),
    }
}

# Static files for desktop (no nginx)
STATIC_ROOT = BASE_DIR / "staticfiles"
```

### 1.3 Environment Selection

```bash
# Development (SQLite)
export DJANGO_SETTINGS_MODULE=PisteMaster.settings.development
python manage.py runserver

# Production (PostgreSQL)
export DJANGO_SETTINGS_MODULE=PisteMaster.settings.production
gunicorn PisteMaster.wsgi:application

# Desktop (SQLite in user data)
export DJANGO_SETTINGS_MODULE=PisteMaster.settings.desktop
python manage.py runserver
```

---

## Phase 2: Electron Desktop Application

### 2.1 Prerequisites

- Node.js 20+
- Python 3.11+ with PyInstaller
- Windows Build Tools (for native modules)

### 2.2 Electron Project Setup

| # | Task | Details | Status |
|---|------|---------|--------|
| 2.2.1 | Create `desktop/` directory | Delete `desktop_app/` first | Pending |
| 2.2.2 | Initialize `desktop/package.json` | electron, electron-builder, electron-updater, vite-plugin-electron | Pending |
| 2.2.3 | Create `electron.vite.config.ts` | Build configuration for Electron | Pending |
| 2.2.4 | Create `src/main/index.ts` | Main process entry point | Pending |
| 2.2.5 | Create `src/preload/index.ts` | Context bridge for IPC | Pending |
| 2.2.6 | Configure TypeScript | `tsconfig.json` for Electron | Pending |

### 2.3 Dependencies

```json
// desktop/package.json
{
  "name": "pistemaster-desktop",
  "version": "0.1.0",
  "description": "PisteMaster - Fencing Tournament Management System",
  "main": "./out/main/index.js",
  "author": "PisteMaster Team",
  "license": "MIT",
  "scripts": {
    "dev": "electron-vite dev",
    "build": "electron-vite build",
    "postinstall": "electron-builder install-app-deps",
    "build:unpack": "npm run build && electron-builder --dir",
    "build:win": "npm run build && electron-builder --win",
    "build:mac": "npm run build && electron-builder --mac",
    "build:linux": "npm run build && electron-builder --linux",
    "release": "npm run build && electron-builder --win --publish always"
  },
  "dependencies": {
    "electron-updater": "^6.1.7"
  },
  "devDependencies": {
    "@electron-toolkit/preload": "^3.0.1",
    "@electron-toolkit/utils": "^3.0.0",
    "@types/node": "^20.11.0",
    "electron": "^28.1.0",
    "electron-builder": "^24.9.1",
    "electron-vite": "^2.0.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}
```

### 2.4 Main Process Structure

```typescript
// desktop/src/main/index.ts
import { app, BrowserWindow, shell, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { setupPythonServer, shutdownPythonServer } from './python-server'
import { setupIpcHandlers } from './ipc-handlers'
import { restoreWindowState, saveWindowState } from './window-state'

let mainWindow: BrowserWindow | null = null
let pythonProcess: ReturnType<typeof setupPythonServer> | null = null

async function createWindow(): Promise<BrowserWindow> {
  // Restore window state (size, position, maximize)
  const windowState = restoreWindowState()
  
  const win = new BrowserWindow({
    width: windowState.width || 1400,
    height: windowState.height || 900,
    x: windowState.x,
    y: windowState.y,
    minWidth: 1024,
    minHeight: 768,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  win.on('ready-to-show', () => {
    win.show()
    if (windowState.isMaximized) {
      win.maximize()
    }
  })

  win.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // Save window state on close
  win.on('close', () => {
    saveWindowState(win)
  })

  // Load the app
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    await win.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    await win.loadFile(join(__dirname, '../renderer/index.html'))
  }

  return win
}

app.whenReady().then(async () => {
  // Set app user model id for Windows
  electronApp.setAppUserModelId('com.pistemaster.app')

  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // Setup IPC handlers
  setupIpcHandlers(ipcMain)

  // Start Python backend in development mode
  if (is.dev) {
    pythonProcess = await setupPythonServer(true)
  }

  // Create main window after Python is ready
  mainWindow = await createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createWindow()
    }
  })
})

app.on('before-quit', async () => {
  await shutdownPythonServer(pythonProcess)
})

// Auto-updater
import { autoUpdater } from 'electron-updater'

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// Check for updates after 3 seconds
setTimeout(() => {
  autoUpdater.checkForUpdatesAndNotify()
}, 3000)

autoUpdater.on('update-available', () => {
  console.log('Update available')
})

autoUpdater.on('update-downloaded', () => {
  mainWindow?.webContents.send('update-available')
})
```

### 2.5 Python Server Management

```typescript
// desktop/src/main/python-server.ts
import { spawn, ChildProcess } from 'child_process'
import { join } from 'path'
import { app } from 'electron'
import { is } from '@electron-toolkit/utils'

const PORT = 8000
const STARTUP_TIMEOUT = 10000

export function setupPythonServer(dev: boolean): Promise<ChildProcess> {
  return new Promise((resolve, reject) => {
    let backendPath: string
    let pythonPath: string

    if (dev) {
      // Development: use system Python and source code
      backendPath = join(__dirname, '../../../../backend')
      pythonPath = 'python' // Use system Python
    } else {
      // Production: use bundled executable
      backendPath = join(process.resourcesPath, 'python')
      pythonPath = join(backendPath, 'pistemaster-backend.exe')
    }

    const env = {
      ...process.env,
      DJANGO_SETTINGS_MODULE: 'PisteMaster.settings.desktop',
      PYTHONUNBUFFERED: '1',
    }

    let process: ChildProcess

    if (dev) {
      process = spawn(pythonPath, ['manage.py', 'runserver', `127.0.0.1:${PORT}`], {
        cwd: backendPath,
        env,
        stdio: ['pipe', 'pipe', 'pipe'],
      })
    } else {
      process = spawn(pythonPath, [], {
        cwd: backendPath,
        env,
        stdio: ['pipe', 'pipe', 'pipe'],
      })
    }

    process.stdout?.on('data', (data) => {
      console.log(`[Python] ${data}`)
      if (data.toString().includes('Starting development server')) {
        resolve(process)
      }
    })

    process.stderr?.on('data', (data) => {
      console.error(`[Python Error] ${data}`)
    })

    process.on('error', (err) => {
      console.error('Failed to start Python server:', err)
      reject(err)
    })

    // Timeout for startup
    setTimeout(() => {
      if (process.pid) {
        resolve(process) // Assume it started
      } else {
        reject(new Error('Python server startup timeout'))
      }
    }, STARTUP_TIMEOUT)
  })
}

export async function shutdownPythonServer(process: ChildProcess | null): Promise<void> {
  if (!process) return
  
  return new Promise((resolve) => {
    process.on('exit', () => resolve())
    
    // Graceful shutdown
    if (process.pid) {
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', process.pid.toString(), '/f', '/t'])
      } else {
        process.kill('SIGTERM')
      }
    }
    
    // Force kill after 5 seconds
    setTimeout(() => {
      if (process.pid) {
        process.kill('SIGKILL')
      }
      resolve()
    }, 5000)
  })
}
```

### 2.6 IPC Handlers

```typescript
// desktop/src/main/ipc-handlers.ts
import { ipcMain, dialog, app } from 'electron'
import { join } from 'path'
import { readdir, unlink, mkdir } from 'fs/promises'
import { existsSync } from 'fs'

export function setupIpcHandlers(ipcMain: IpcMain): void {
  // Get app version
  ipcMain.handle('get-app-version', () => {
    return app.getVersion()
  })

  // Get user data directory
  ipcMain.handle('get-user-data-path', () => {
    return app.getPath('userData')
  })

  // Get database path
  ipcMain.handle('get-database-path', () => {
    return join(app.getPath('userData'), 'data', 'pistemaster.db')
  })

  // Open file dialog for import
  ipcMain.handle('open-file-dialog', async (_event, options: {
    title?: string
    filters?: { name: string; extensions: string[] }[]
    multiSelections?: boolean
  }) => {
    const result = await dialog.showOpenDialog({
      title: options?.title || 'Select File',
      filters: options?.filters || [{ name: 'All Files', extensions: ['*'] }],
      properties: [
        'openFile',
        ...(options?.multiSelections ? ['multiSelections'] as const : [])
      ],
    })
    return result.filePaths
  })

  // Save file dialog for export
  ipcMain.handle('save-file-dialog', async (_event, options: {
    title?: string
    defaultPath?: string
    filters?: { name: string; extensions: string[] }[]
  }) => {
    const result = await dialog.showSaveDialog({
      title: options?.title || 'Save File',
      defaultPath: options?.defaultPath,
      filters: options?.filters || [{ name: 'All Files', extensions: ['*'] }],
    })
    return result.filePath
  })

  // Clear application data
  ipcMain.handle('clear-app-data', async () => {
    const userDataPath = app.getPath('userData')
    const dbPath = join(userDataPath, 'data', 'pistemaster.db')
    
    if (existsSync(dbPath)) {
      await unlink(dbPath)
    }
    
    return { success: true }
  })

  // Quit and install update
  ipcMain.on('quit-and-install', () => {
    require('electron-updater').autoUpdater.quitAndInstall()
  })
}
```

### 2.7 Preload Script

```typescript
// desktop/src/preload/index.ts
import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

// Custom APIs for renderer
const api = {
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getUserDataPath: () => ipcRenderer.invoke('get-user-data-path'),
  getDatabasePath: () => ipcRenderer.invoke('get-database-path'),
  
  openFileDialog: (options?: {
    title?: string
    filters?: { name: string; extensions: string[] }[]
    multiSelections?: boolean
  }) => ipcRenderer.invoke('open-file-dialog', options),
  
  saveFileDialog: (options?: {
    title?: string
    defaultPath?: string
    filters?: { name: string; extensions: string[] }[]
  }) => ipcRenderer.invoke('save-file-dialog', options),
  
  clearAppData: () => ipcRenderer.invoke('clear-app-data'),
  quitAndInstall: () => ipcRenderer.send('quit-and-install'),
  
  onUpdateAvailable: (callback: () => void) => {
    ipcRenderer.on('update-available', callback)
  },
}

// Use `contextBridge` APIs to expose Electron APIs to renderer
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', {
      ...electronAPI,
      ...api,
    })
  } catch (error) {
    console.error('Failed to expose API:', error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = {
    ...electronAPI,
    ...api,
  }
}
```

### 2.8 Vite Configuration

```typescript
// desktop/electron.vite.config.ts
import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
    resolve: {
      alias: {
        '@': resolve('src/main'),
      },
    },
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    resolve: {
      alias: {
        '@': resolve('src/preload'),
      },
    },
  },
  renderer: {
    root: resolve(__dirname, '../web_frontend'),
    build: {
      rollupOptions: {
        input: {
          index: resolve(__dirname, '../web_frontend/index.html'),
        },
      },
    },
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, '../web_frontend/src'),
      },
    },
    server: {
      port: 3001,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  },
})
```

### 2.9 electron-builder Configuration

```yaml
# desktop/electron-builder.yml
appId: com.pistemaster.app
productName: PisteMaster
copyright: Copyright © 2026 PisteMaster

directories:
  buildResources: resources
  output: release

# Windows configuration
win:
  icon: resources/icons/icon.ico
  target:
    - target: nsis
      arch:
        - x64
        - ia32
  artifactName: ${productName}-Setup-${version}.${ext}

# NSIS installer configuration
nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
  perMachine: false
  installerIcon: resources/icons/icon.ico
  uninstallerIcon: resources/icons/icon.ico
  installerHeaderIcon: resources/icons/icon.ico
  createDesktopShortcut: true
  createStartMenuShortcut: true
  shortcutName: ${productName}

# Include Python backend
extraResources:
  - from: "../backend/dist/pistemaster-backend"
    to: "python"
    filter:
      - "**/*"

# Auto-update configuration
publish:
  provider: github
  owner: pistemaster
  repo: pistemaster
  releaseType: release

# Files to include
files:
  - "!**/.vscode/*"
  - "!**/node_modules/*"
  - "!**/src/*"
  - "out/**/*"
  - "package.json"

# Before build hook - build Python backend
beforeBuild: "./scripts/prebuild.js"
```

---

## Phase 3: PyInstaller Backend Bundle

### 3.1 PyInstaller Configuration

| # | Task | Details | Status |
|---|------|---------|--------|
| 3.1.1 | Create `PisteMaster.spec` | PyInstaller spec file | Pending |
| 3.1.2 | Create `scripts/build-python.ps1` | Windows build script | Pending |
| 3.1.3 | Update `requirements.txt` | Include PyInstaller | Pending |
| 3.1.4 | Create standalone entry point | `run_desktop.py` | Pending |

### 3.2 Desktop Entry Point

```python
# backend/run_desktop.py
"""
Entry point for desktop application (bundled with PyInstaller)
"""
import os
import sys
from pathlib import Path

# Set settings module before Django imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PisteMaster.settings.desktop')

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def get_data_dir():
    """Get platform-specific data directory."""
    app_name = "PisteMaster"
    home = Path.home()
    
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', home))
    elif sys.platform == 'darwin':
        base = home / 'Library' / 'Application Support'
    else:
        base = home / '.local' / 'share'
    
    return base / app_name / 'data'

def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def main():
    # Ensure data directory exists
    data_dir = ensure_data_dir()
    
    # Database path
    db_path = data_dir / 'pistemaster.db'
    
    # Run migrations if needed
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'migrate', '--noinput'])
    
    # Start server
    from django.core.management import execute_from_command_line
    port = int(os.environ.get('DJANGO_PORT', 8000))
    execute_from_command_line(['manage.py', 'runserver', f'127.0.0.1:{port}', '--nothreading'])

if __name__ == '__main__':
    main()
```

### 3.3 PyInstaller Spec File

```python
# backend/PisteMaster.spec
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Get the backend directory
backend_dir = Path('.').resolve()

a = Analysis(
    ['run_desktop.py'],
    pathex=[str(backend_dir)],
    binaries=[],
    datas=[
        # Include static files and templates
        ('static', 'static'),
        ('templates', 'templates'),
        # Include locale files if any
        ('locale', 'locale'),
    ],
    hiddenimports=[
        'django',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'rest_framework',
        'corsheaders',
        'django_filters',
        'backend.apps.fencing_organizer',
        'core',
    ],
    hookspath=['./hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='pistemaster-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Enable UPX compression
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console for debugging, set to False for release
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

### 3.4 Build Scripts

```powershell
# scripts/build-python.ps1
# Windows PowerShell script to build Python backend

param(
    [string]$Configuration = "Release"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$DistDir = Join-Path $BackendDir "dist"

Write-Host "Building Python backend..." -ForegroundColor Cyan

# Create virtual environment if not exists
$VenvDir = Join-Path $BackendDir "venv_build"
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $VenvDir
}

# Activate virtual environment
& "$VenvDir\Scripts\Activate.ps1"

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r "$BackendDir\requirements.txt"
pip install pyinstaller

# Build executable
Write-Host "Running PyInstaller..." -ForegroundColor Yellow
Set-Location $BackendDir
pyinstaller PisteMaster.spec --noconfirm --clean

# Check result
if (Test-Path "$DistDir\pistemaster-backend.exe") {
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "Output: $DistDir\pistemaster-backend.exe" -ForegroundColor Green
} else {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

# Deactivate
deactivate
```

```bash
# scripts/build-python.sh
#!/bin/bash
# Linux/macOS script to build Python backend

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
DIST_DIR="$BACKEND_DIR/dist"

echo "Building Python backend..."

# Create virtual environment if not exists
VENV_DIR="$BACKEND_DIR/venv_build"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"
pip install pyinstaller

# Build executable
echo "Running PyInstaller..."
cd "$BACKEND_DIR"
pyinstaller PisteMaster.spec --noconfirm --clean

# Check result
if [ -f "$DIST_DIR/pistemaster-backend" ]; then
    echo "Build successful!"
    echo "Output: $DIST_DIR/pistemaster-backend"
else
    echo "Build failed!"
    exit 1
fi

# Deactivate
deactivate
```

---

## Phase 4: CI/CD Pipeline (GitHub Actions)

### 4.1 Workflow Structure

```
.github/workflows/
├── build-desktop.yml     # Build and test Electron app
├── build-web.yml         # Build Docker images
└── release.yml           # Create releases with installers
```

### 4.2 Desktop Build Workflow

```yaml
# .github/workflows/build-desktop.yml
name: Build Desktop Application

on:
  push:
    branches: [main, develop]
    paths:
      - 'web_frontend/**'
      - 'backend/**'
      - 'core/**'
      - 'desktop/**'
      - '.github/workflows/build-desktop.yml'
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      configuration:
        description: 'Build configuration'
        required: true
        default: 'Release'
        type: choice
        options:
          - Debug
          - Release

env:
  NODE_VERSION: '20'
  PYTHON_VERSION: '3.11'

jobs:
  # Job 1: Build Python Backend
  build-python:
    runs-on: windows-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        working-directory: ./backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Build backend executable
        working-directory: ./backend
        run: pyinstaller PisteMaster.spec --noconfirm --clean

      - name: Upload backend artifact
        uses: actions/upload-artifact@v4
        with:
          name: backend-windows
          path: backend/dist/pistemaster-backend.exe
          retention-days: 7

  # Job 2: Build Vue Frontend
  build-frontend:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: 'web_frontend/package-lock.json'

      - name: Install dependencies
        working-directory: ./web_frontend
        run: npm ci

      - name: Build Vue app
        working-directory: ./web_frontend
        run: npm run build

      - name: Upload frontend artifact
        uses: actions/upload-artifact@v4
        with:
          name: frontend-build
          path: web_frontend/dist/
          retention-days: 7

  # Job 3: Build Electron Package
  build-electron:
    needs: [build-python, build-frontend]
    runs-on: windows-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: 'desktop/package-lock.json'

      - name: Download backend artifact
        uses: actions/download-artifact@v4
        with:
          name: backend-windows
          path: backend/dist/

      - name: Download frontend artifact
        uses: actions/download-artifact@v4
        with:
          name: frontend-build
          path: web_frontend/dist/

      - name: Install desktop dependencies
        working-directory: ./desktop
        run: npm ci

      - name: Build Electron app
        working-directory: ./desktop
        run: npm run build:win

      - name: Upload installer artifact
        uses: actions/upload-artifact@v4
        with:
          name: pistemaster-installer
          path: desktop/release/*.exe
          retention-days: 30

  # Job 4: Test the build
  test-electron:
    needs: build-electron
    runs-on: windows-latest
    steps:
      - name: Download installer artifact
        uses: actions/download-artifact@v4
        with:
          name: pistemaster-installer
          path: ./installer/

      - name: Install application
        run: |
          $installer = Get-ChildItem ./installer/*.exe | Select-Object -First 1
          Start-Process -FilePath $installer.FullName -ArgumentList '/S' -Wait
        shell: pwsh

      - name: Verify installation
        run: |
          $appPath = "$env:LOCALAPPDATA\Programs\PisteMaster\PisteMaster.exe"
          if (Test-Path $appPath) {
            Write-Host "Application installed successfully"
          } else {
            Write-Error "Application not found at $appPath"
            exit 1
          }
        shell: pwsh
```

### 4.3 Release Workflow

```yaml
# .github/workflows/release.yml
name: Create Release

on:
  push:
    tags:
      - 'v*.*.*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Version number (e.g., 0.1.0)'
        required: true
        type: string

permissions:
  contents: write

jobs:
  build:
    uses: ./.github/workflows/build-desktop.yml
    with:
      configuration: Release

  create-release:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Get version
        id: version
        run: |
          if [ "${{ github.event_name }}" == "workflow_dispatch" ]; then
            echo "VERSION=${{ github.event.inputs.version }}" >> $GITHUB_OUTPUT
          else
            echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT
          fi

      - name: Download installer artifact
        uses: actions/download-artifact@v4
        with:
          name: pistemaster-installer
          path: ./release/

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: v${{ steps.version.outputs.VERSION }}
          name: PisteMaster v${{ steps.version.outputs.VERSION }}
          body: |
            ## PisteMaster v${{ steps.version.outputs.VERSION }}
            
            ### What's Changed
            See [CHANGELOG.md](./CHANGELOG.md) for details.
            
            ### Installation
            Download `PisteMaster-Setup-${{ steps.version.outputs.VERSION }}.exe` and run the installer.
            
            ### System Requirements
            - Windows 10 or later (64-bit recommended)
            - 500MB free disk space
            
          draft: false
          prerelease: ${{ contains(steps.version.outputs.VERSION, '-') }}
          files: |
            ./release/*.exe
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Update version file
        run: |
          echo "${{ steps.version.outputs.VERSION }}" > VERSION
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add VERSION
          git commit -m "chore: update version to ${{ steps.version.outputs.VERSION }}"
          git push
```

### 4.4 Build Web Workflow (Docker)

```yaml
# .github/workflows/build-web.yml
name: Build Web Application (Docker)

on:
  push:
    branches: [main]
    paths:
      - 'web_frontend/**'
      - 'backend/**'
      - 'core/**'
      - 'docker-compose.yml'
      - '.github/workflows/build-web.yml'
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  NODE_VERSION: '20'
  PYTHON_VERSION: '3.11'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: 'web_frontend/package-lock.json'

      - name: Install dependencies
        working-directory: ./web_frontend
        run: npm ci

      - name: Run linter
        working-directory: ./web_frontend
        run: npm run lint

  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt
          pip install pytest pytest-django

      - name: Run backend tests
        run: pytest tests/ -v

  build-docker:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ secrets.DOCKER_USERNAME }}/pistemaster
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile.web
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## Phase 5: Auto-Update System

### 5.1 Overview

The desktop application uses `electron-updater` to check for updates from GitHub Releases. When a new version is published:

1. Application checks for updates on startup
2. If update available, downloads in background
3. Notifies user when ready to install
4. User can choose to install now or later

### 5.2 Implementation

| # | Task | Details | Status |
|---|------|---------|--------|
| 5.2.1 | Add auto-update check in `main/index.ts` | `autoUpdater.checkForUpdatesAndNotify()` | Pending |
| 5.2.2 | Add update notification UI | Show dialog when update downloaded | Pending |
| 5.2.3 | Configure `electron-builder.yml` | Set `publish.provider: github` | Pending |
| 5.2.4 | Test update flow | Publish test release, verify update | Pending |

### 5.3 Update UI Component

```vue
<!-- web_frontend/src/components/common/UpdateNotification.vue -->
<template>
  <el-dialog
    v-model="visible"
    title="Update Available"
    width="400px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <p>A new version of PisteMaster is available!</p>
    <p>Version {{ updateInfo?.version }} has been downloaded.</p>
    
    <template #footer>
      <el-button @click="later">Later</el-button>
      <el-button type="primary" @click="install">Restart & Install</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const visible = ref(false)
const updateInfo = ref<{ version: string } | null>(null)

onMounted(() => {
  if (window.electron?.onUpdateAvailable) {
    window.electron.onUpdateAvailable(() => {
      visible.value = true
    })
  }
})

const later = () => {
  visible.value = false
}

const install = () => {
  visible.value = false
  if (window.electron?.quitAndInstall) {
    window.electron.quitAndInstall()
  }
}
</script>
```

---

## Phase 6: Development Workflow

### 6.1 Development Scripts

Update root `package.json`:

```json
{
  "name": "pistemaster",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "concurrently \"npm run dev:backend\" \"npm run dev:frontend\"",
    "dev:backend": "cd backend && python manage.py runserver",
    "dev:frontend": "cd web_frontend && npm run dev",
    "dev:electron": "cd desktop && npm run dev",
    "build": "npm run build:python && npm run build:electron",
    "build:python": "./scripts/build-python.ps1",
    "build:electron": "cd desktop && npm run build:win",
    "release": "npm version patch && git push --follow-tags",
    "install:all": "npm install && cd web_frontend && npm install && cd ../desktop && npm install"
  },
  "devDependencies": {
    "concurrently": "^8.2.0"
  }
}
```

### 6.2 Daily Development Commands

```bash
# Start both backend and frontend (web development)
npm run dev

# Start Electron with live reload (desktop development)
npm run dev:electron

# Build Python backend
npm run build:python

# Build Electron installer
npm run build:electron

# Create a new release (bumps version, creates tag)
npm run release
```

### 6.3 Release Process

```bash
# 1. Ensure all changes are committed
git status

# 2. Run tests
npm test

# 3. Update version
npm version patch  # or minor/major

# 4. Push with tags
git push --follow-tags

# 5. GitHub Actions will:
#    - Build Python backend
#    - Build Electron app
#    - Create GitHub Release
#    - Upload installer as asset
```

---

## Build Commands Reference

### Web Version (Docker)

```bash
# Build and run
docker-compose up --build

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Desktop Version (Electron)

```bash
# Development mode (with live reload)
cd desktop && npm run dev

# Build without packaging (for testing)
cd desktop && npm run build:unpack

# Build Windows installer
cd desktop && npm run build:win

# Build macOS app (for future)
cd desktop && npm run build:mac

# Build Linux package (for future)
cd desktop && npm run build:linux
```

---

## File Checklist

### Files to Create

| File | Purpose |
|------|---------|
| `desktop/package.json` | Electron project configuration |
| `desktop/electron.vite.config.ts` | Vite configuration for Electron |
| `desktop/tsconfig.json` | TypeScript configuration |
| `desktop/src/main/index.ts` | Electron main process |
| `desktop/src/main/app.ts` | App lifecycle management |
| `desktop/src/main/python-server.ts` | Django subprocess management |
| `desktop/src/main/ipc-handlers.ts` | Native operations handlers |
| `desktop/src/main/window-state.ts` | Window position/size persistence |
| `desktop/src/preload/index.ts` | Context bridge |
| `desktop/electron-builder.yml` | Build configuration |
| `backend/PisteMaster.spec` | PyInstaller spec file |
| `backend/run_desktop.py` | Desktop entry point |
| `backend/PisteMaster/settings/base.py` | Common Django settings |
| `backend/PisteMaster/settings/development.py` | Development settings |
| `backend/PisteMaster/settings/production.py` | Production (PostgreSQL) settings |
| `backend/PisteMaster/settings/desktop.py` | Desktop (SQLite) settings |
| `.github/workflows/build-desktop.yml` | GitHub Actions workflow |
| `.github/workflows/build-web.yml` | Docker build workflow |
| `.github/workflows/release.yml` | Release automation |
| `scripts/build-python.ps1` | Windows Python build script |
| `scripts/build-python.sh` | Unix Python build script |
| `scripts/prebuild.js` | Electron-builder pre-build hook |

### Files to Modify

| File | Changes |
|------|---------|
| `backend/PisteMaster/settings.py` | Import from settings modules |
| `backend/requirements.txt` | Add PyInstaller |
| `web_frontend/src/main.ts` | Add Electron detection |
| `web_frontend/src/services/DataManager.ts` | Dynamic API URL |
| `package.json` | Add build scripts |

### Files to Delete

| File/Directory | Reason |
|----------------|--------|
| `desktop_app/` | Replaced by `desktop/` |

---

## Testing Checklist

### Desktop Application

- [ ] App launches correctly on Windows
- [ ] Python backend starts automatically
- [ ] All web features work offline
- [ ] Database persists between sessions (`%APPDATA%/PisteMaster/data/`)
- [ ] Clean shutdown (backend process killed)
- [ ] Window size/position remembered
- [ ] Auto-update notification works
- [ ] File dialogs work (import/export)
- [ ] Windows installer runs correctly
- [ ] Uninstaller removes all data

### Web Application (Docker)

- [ ] docker-compose up succeeds
- [ ] PostgreSQL migrations run
- [ ] Tournament CRUD operations work
- [ ] Event management works
- [ ] Fencer import works
- [ ] Pool generation and scoring work
- [ ] DE bracket visualization works
- [ ] Final ranking calculation works

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| 1. Database Config | 2 days | None |
| 2. Electron Setup | 3 days | None |
| 3. PyInstaller Bundle | 2 days | Phase 2 |
| 4. CI/CD Pipeline | 2 days | Phase 2, 3 |
| 5. Auto-Update | 1 day | Phase 4 |
| 6. Testing & Polish | 2 days | All phases |
| **Total** | **12 days** | |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| PyInstaller bundle size too large | Slow download/install | Use UPX compression; exclude unnecessary packages |
| Antivirus false positives | Users can't install | Document workaround; consider signing later |
| Python port conflicts | Backend won't start | Use dynamic port allocation; check if port is free |
| Database migration issues | Data loss on update | Include backup/restore in migration logic |
| Windows code signing | "Unknown publisher" warning | Start without signing; plan for certificate purchase |
| Electron memory usage | Slower than native | Optimize bundle; consider lazy loading |
| Auto-update failures | Users on old versions | Add manual update check option |

---

## Post-MVP Roadmap

### Priority 1: Architecture Improvements

1. **Monorepo Setup (HIGH PRIORITY)** - Migrate to proper monorepo structure
   - Current state: `desktop/` duplicates some Vue dependencies from `web_frontend/`
   - Target state: Shared dependencies via npm workspaces or pnpm workspaces
   - Benefits: Smaller bundle size, easier maintenance, shared build config
   - See [Appendix C: Monorepo Migration Plan](#appendix-c-monorepo-migration-plan) for details

2. **Code Signing** - Purchase certificate, add to CI/CD

### Priority 2: Platform Support

3. **macOS Support** - Add macOS build target, notarize app
4. **Linux Support** - Add AppImage/deb build targets

### Priority 3: Feature Enhancements

5. **Team Events** - Team brackets, relay matches
6. **Authentication** - JWT-based user system
7. **Piste/Referee Management** - Assignment and scheduling
8. **Live Scoreboard** - WebSocket real-time updates
9. **Distributed Mode** - Multi-client coordination

---

## Appendix A: VERSION File

```
# VERSION file (created by CI/CD)
0.1.0
```

## Appendix B: CHANGELOG Template

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.1.0] - 2026-03-XX

### Added
- Initial MVP release
- Electron desktop application for Windows
- Embedded Django backend with SQLite
- Tournament, event, and fencer management
- Pool generation and scoring
- Direct elimination brackets
- Final ranking calculation
- Offline support for tournament venues
```

---

## Appendix C: Monorepo Migration Plan

### Current Architecture Issues

1. **Dependency Duplication**
   - `desktop/package.json` duplicates Vue dependencies from `web_frontend/package.json`
   - Two separate `node_modules` directories increase disk usage
   - Version mismatches can cause bugs

2. **Build Complexity**
   - Separate build commands for each package
   - No shared build configuration
   - Difficult to ensure consistent versions across projects

3. **Development Workflow**
   - Need to run `npm install` in multiple directories
   - No single source of truth for dependency versions

### Target Monorepo Structure

```
PisteMaster/
├── packages/
│   ├── web/                    # Vue web application (renamed from web_frontend)
│   │   ├── src/
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   ├── desktop/                # Electron desktop application
│   │   ├── src/
│   │   │   ├── main/           # Electron main process
│   │   │   └── preload/        # Preload scripts
│   │   ├── package.json
│   │   └── electron.vite.config.ts
│   │
│   └── shared/                 # Shared utilities and types
│       ├── src/
│       │   ├── types/          # TypeScript interfaces
│       │   ├── utils/          # Utility functions
│       │   └── constants/      # Shared constants
│       └── package.json
│
├── backend/                    # Django backend (unchanged)
├── core/                      # Python domain models (unchanged)
│
├── package.json                # Root package.json (workspace config)
├── pnpm-workspace.yaml         # pnpm workspace config (optional)
└── turbo.json                 # Turborepo config (optional)
```

### Migration Steps

| Step | Description | Effort |
|------|-------------|--------|
| 1 | Create root `pnpm-workspace.yaml` or npm workspaces in root `package.json` | 1 day |
| 2 | Move `web_frontend/` to `packages/web/` | 1 day |
| 3 | Move `desktop/` to `packages/desktop/` | 1 day |
| 4 | Create `packages/shared/` with common types | 2 days |
| 5 | Extract common dependencies to root `package.json` | 1 day |
| 6 | Update all import paths and build configs | 2 days |
| 7 | Update CI/CD workflows for monorepo | 1 day |
| 8 | Test all packages and fix issues | 2 days |

**Total Estimated Effort: 10-12 days**

### Benefits of Monorepo

| Benefit | Description |
|---------|-------------|
| Shared dependencies | Vue, TypeScript, ESLint installed once |
| Type sharing | `packages/shared/` exports types used by both web and desktop |
| Unified builds | Single `npm run build` builds all packages |
| Consistent versions | No version mismatches between packages |
| Easier refactoring | Changes propagate across all packages |
| Better DX | Single `npm install` at root |

### Monorepo Tools Comparison

| Tool | Pros | Cons |
|------|------|------|
| **npm workspaces** | Built into npm, no extra tool | Limited features, slower than pnpm |
| **pnpm workspaces** | Fast, efficient disk usage, strict dependencies | Need to learn pnpm |
| **Turborepo** | Parallel builds, caching, great DX | Additional learning curve |
| **Nx** | Full-featured, great for large monorepos | Complex setup, overkill for small teams |

### Recommended Stack

For PisteMaster, we recommend:

1. **pnpm workspaces** - Fast, efficient, handles dependencies well
2. **Turborepo** (optional) - Add later if build times become an issue

### Migration Commands

```bash
# Step 1: Install pnpm globally
npm install -g pnpm

# Step 2: Create workspace config
cat > pnpm-workspace.yaml << EOF
packages:
  - 'packages/*'
EOF

# Step 3: Create root package.json with workspace references
cat > package.json << EOF
{
  "name": "pistemaster-monorepo",
  "private": true,
  "scripts": {
    "dev": "pnpm --filter \"./packages/*\" dev",
    "build": "pnpm --filter \"./packages/*\" build",
    "lint": "pnpm --filter \"./packages/*\" lint"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vue": "^3.4.0"
  }
}
EOF

# Step 4: Move packages
mkdir -p packages
mv web_frontend packages/web
mv desktop packages/desktop

# Step 5: Install dependencies
pnpm install

# Step 6: Verify
pnpm run build
```

### Shared Package Example

```typescript
// packages/shared/src/types/tournament.ts
export interface Tournament {
  id: string
  tournament_name: string
  status: 'draft' | 'active' | 'completed'
  start_date: string
  end_date: string
}

// packages/web/src/views/TournamentList.vue
import type { Tournament } from '@pistemaster/shared/types/tournament'

// packages/desktop/src/main/ipc-handlers.ts
import type { Tournament } from '@pistemaster/shared/types/tournament'
```

### Rollback Plan

If migration fails:
1. Revert to separate package structure
2. Each package maintains its own `node_modules`
3. No shared code between web and desktop

---

*End of MVP Build Plan v2.0*