# PisteMaster Build Guide

This document explains how to build PisteMaster for both Desktop (Electron) and Web (Docker) versions.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Desktop Version (Electron)](#desktop-version-electron)
- [Web Version (Docker)](#web-version-docker)
- [Development Mode](#development-mode)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### ForDesktop Version
- Node.js 20+
- Python 3.11+
- Windows 10/11 (for Windows build)
- **Windows Developer Mode** enabled (required for electron-builder symlinks)

### ForWeb Version
- Docker and Docker Compose
- (Optional) WSL2 on Windows for Docker

---

## Desktop Version (Electron)

### 1. Enable Windows Developer Mode

**Required for electron-builder symlinks:**
1. Open WindowsSettings
2. Go to **更新和安全** → **开发者选项**
3. Enable **开发人员模式**

### 2. Install Dependencies

```bash
# Installall dependencies
npm run install:all

# Or manually:
cd web_frontend && npm install
cd ../desktop && npm install
```

### 3. Build Frontend for Desktop

```bash
cd web_frontend
npm run build
```

### 4. Build Electron App

```bash
cd desktop
npm run build
npm run build:win
```

This produces:
- `desktop/release/win-unpacked/` - Portable version (runs without installation)
- `desktop/release/PisteMaster-Setup-{version}.exe` - NSIS installer

### 5. Output Files

| File | Description |
|------|-------------|
| `win-unpacked/PisteMaster.exe` | Portable executable |
| `PisteMaster-Setup-0.1.0.exe` | Windows installer |
| `PisteMaster-Setup-0.1.0.exe.blockmap` | For auto-updates |

### 6. Testing

```bash
# Run portable version
.\desktop\release\win-unpacked\PisteMaster.exe

# Or install and run
.\desktop\release\PisteMaster-Setup-0.1.0.exe
```

### Common Commands

```bash
# Development mode
cd desktop && npm run dev

# Build without packaging (faster for testing)
cd desktop && npm run build:unpack

# Build Windows installer
cd desktop && npm run build:win

# Build macOS (requires macOS)
cd desktop && npm run build:mac

# Build Linux
cd desktop && npm run build:linux
```

---

## Web Version (Docker)

### 1. Build Frontend for Production

```bash
cd web_frontend
npx vite build
```

### 2. Start Docker Containers

```bash
# Build and start all services
sudo docker compose up --build

# Or for Windows PowerShell:
docker compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **Django backend** on port 8000
- **Nginx frontend** on port 8080

### 3. Initialize Database

```bash
# Run migrations
sudo docker compose exec backend python manage.py migrate

# Create admin user
sudo docker compose exec backend python manage.py createsuperuser
```

### 4. Access the Application

- **Frontend:** http://localhost:8080 (orhttp://<WSL_IP>:8080 from Windows)
- **Backend API:** http://localhost:8000/api
- **Swagger Docs:** http://localhost:8000/swagger
- **Admin Panel:** http://localhost:8000/admin

### 5. Stop Containers

```bash
# Stop containers (preserves data)
sudo docker compose down

# Stop and remove all data
sudo docker compose down -v
```

### WSL2 Networking

If running Docker in WSL2 and accessing from Windows browser:

1. Get WSL IP address:
```bash
ip addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'
```

2. Access via WSL IP: `http://<WSL_IP>:8080`

### Configuration Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Docker orchestration config |
| `backend/Dockerfile` | Django container image |
| `backend/requirements-docker.txt` | Python dependencies for Docker |
| `nginx.conf` | Reverse proxy configuration |
| `.env.docker` | Environment variables template |

---

## Development Mode

### Desktop Development

```bash
# Terminal 1: Start Django backend
cd backend
python manage.py runserver

# Terminal 2: Start Electron in dev mode
cd desktop
npm run dev
```

### Web Development

```bash
# Terminal 1: Start Django backend
cd backend
python manage.py runserver

# Terminal 2: Start Vue frontend
cd web_frontend
npm run dev
```

### Combined Development

```bash
# From project root
npm run dev
```

---

## Troubleshooting

### Desktop Build Issues

**Symkink permission error:**
```
ERROR: Cannot create symbolic link :客户端没有所需的特权
```
**Solution:** Enable Windows Developer Mode (see Prerequisites).

**Python backend not found:**
```
Error: Python server startup timeout
```
**Solution:** Build Python backend first:
```bash
cd backend
pyinstaller PisteMaster.spec --noconfirm --clean
```

### Web/Docker Issues

**CORS errors:**
- Check `CORS_ALLOWED_ORIGINS` in `docker-compose.yml`
- For development, use `CORS_ALLOWED_ORIGINS: "*"`

**CSRF errors:**
- API uses `CsrfExemptSessionAuthentication` for cross-origin requests
- Check `CSRF_TRUSTED_ORIGINS` includes your origin

**Can't connect from Windows browser:**
- Use WSL IP address instead of localhost
- Check `ALLOWED_HOSTS` includes theIP

**Database connection errors:**
- Ensure PostgreSQL container is healthy: `docker compose logs postgres`
- Check credentials match in `docker-compose.yml`

### Port Conflicts

If ports are already in use:

```bash
# Check what's using the port
netstat -ano | findstr :8080

# Change ports in docker-compose.yml
ports:
  - "8081:80"  # Change from 8080 to 8081
```

---

## Build Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Desktop Version                          │
├─────────────────────────────────────────────────────────────┤
│  Electron + Vue3 Frontend                                  │
│  └── Bundled Python (PyInstaller) + Django + SQLite       │
│      └── Single executable / installer                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Web Version                               │
├─────────────────────────────────────────────────────────────┤
│  Nginx (port 8080)                                          │
│  ├── Serves Vue3static files                               │
│  └── Proxies /api/*→ Django                               │
│      └── Django (port 8000)                                 │
│          └── PostgreSQL (port 5432)                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Reference

### Desktop Build (One-liner)

```bash
cd web_frontend && npx vite build && cd ../desktop && npm run build:win
```

### Web Build (One-liner)

```bash
cd web_frontend && npx vite build && cd .. && sudo docker compose up --build
```

---

## Environment Variables

### Desktop (.env.development)

```
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_DEBUG=true
```

### Web (.env.production)

```
VITE_API_BASE_URL=/api
VITE_DEBUG=false
VITE_OFFLINE_MODE=true
```

### DockerCompose

See `.env.docker` for template. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | Required | Django secret key |
| `DEBUG` | False | Django debug mode |
| `POSTGRES_DB` | pistemaster | Database name |
| `POSTGRES_USER` | pistemaster | Database user |
| `POSTGRES_PASSWORD` | pistemaster123 | Database password |
| `CORS_ALLOWED_ORIGINS` | * | Allowed CORS origins |
| `CSRF_TRUSTED_ORIGINS` | localhost:8080 | Trusted CSRF origins |