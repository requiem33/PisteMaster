---
name: launch-app-skill
description: use this to start the frontend and backend servers
---

# Kill running processes:

## Kill Django backend (usually port 8000)

```bash
pkill -f "manage.py runserver" || true
```

## Kill Vue frontend (port 3001)

```bash
pkill -f "vite" || true
```

# Backend with venv:

```bash
source venv/bin/activate
cd backend
rm -f db.sqlite3
python manage.py migrate
python manage.py runserver &
```

# Frontend:

```bash
cd web_frontend && npm run dev &
```