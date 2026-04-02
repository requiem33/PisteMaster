# User System Architecture

## Overview

PisteMaster implements a role-based access control (RBAC) system with three user types for the MVP release.

## User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access: create/edit/delete all tournaments, manage users (CRUD), assign schedulers |
| **Scheduler** | Create tournaments, edit tournaments where assigned (creator or in schedulers list) |
| **Guest** | Browse only (unauthenticated read-only access) |

## Architecture

### Backend (Django)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Django Backend                            │
├─────────────────────────────────────────────────────────────────┤
│  Users App:                                                      │
│  - Custom User model (AbstractUser + role field)                 │
│  - AuthViewSet: login, logout, me endpoints                      │
│  - UserViewSet: CRUD for admin only                              │
├─────────────────────────────────────────────────────────────────┤
│  Tournament Model Extensions:                                    │
│  - created_by: FK to User (tournament creator)                  │
│  - schedulers: M2M to User (users who can edit)                 │
├─────────────────────────────────────────────────────────────────┤
│  Permission Classes:                                              │
│  - IsAdmin: Admin only                                           │
│  - IsSchedulerOrAdmin: Scheduler or Admin for creation          │
│  - IsTournamentEditor: Object-level for edit permissions        │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend (Web & Desktop Shared)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Vue 3 Frontend                            │
├─────────────────────────────────────────────────────────────────┤
│  Platform Detection (src/utils/platform.ts):                    │
│  - isElectron(): boolean - detects Electron environment         │
│  - isDesktop = isElectron() - for conditional rendering         │
├─────────────────────────────────────────────────────────────────┤
│  Auth Store (Pinia):                                              │
│  - user state, isAuthenticated, isAdmin, isScheduler, isGuest   │
│  - isDesktop: computed from platform detection                  │
│  - login, logout, fetchCurrentUser actions                       │
│  - initGuestUser(): called on desktop when not authenticated   │
├─────────────────────────────────────────────────────────────────┤
│  Auth Service:                                                    │
│  - login(username, password) → User                              │
│  - logout() → void                                               │
│  - getCurrentUser() → User | null                               │
├─────────────────────────────────────────────────────────────────┤
│  Desktop Auth Service (Electron only):                          │
│  - getLocalUser() → LocalUser (via Electron IPC)               │
│  - clearLocalUser() → void                                       │
│  - updateLocalUsername(username) → LocalUser                    │
├─────────────────────────────────────────────────────────────────┤
│  Route Guards:                                                    │
│  - Web: Redirect unauthenticated users to /login                │
│  - Desktop: Allow guest users for most routes                   │
│  - Preserve redirect target in query params                      │
│  - Admin-only routes check                                       │
├─────────────────────────────────────────────────────────────────┤
│  Components:                                                      │
│  - Login.vue: Login form + "Continue as Guest" on desktop      │
│  - UserMenu.vue: User info + logout (or login for guests)       │
└─────────────────────────────────────────────────────────────────┘
```

### Desktop App vs Web App Behavior

**Web App (Browser):**
- Unauthenticated users can only **browse** public tournaments (read-only)
- No "guest" user concept - users are either logged in or anonymous
- All write operations require authentication via Django backend
- User display: Shows username + role badge when logged in, "Login" button when not

**Desktop App (Electron):**
- Unauthenticated users become **guest users** automatically
- Guest users can **create local tournaments** stored in local SQLite
- Guest tournaments can later be synced to server after logging in
- User display: Shows "Guest_abc123" badge with option to customize username or login

```
┌─────────────────────────────────────────────────────────────────┐
│                      Electron Desktop App                         │
├─────────────────────────────────────────────────────────────────┤
│  Environment Detection:                                           │
│  - isElectron() returns true when running in Electron             │
│  - Web app ignores guest user functionality                       │
├─────────────────────────────────────────────────────────────────┤
│  Local SQLite Database (always available):                       │
│  - Offline tournament creation with guest user                   │
│  - Local tournaments stored with localUser.id                    │
├─────────────────────────────────────────────────────────────────┤
│  Electron IPC API (main → preload → renderer):                   │
│  - auth:getLocalUser(): Generate or retrieve guest user          │
│  - auth:clearLocalUser(): Clear on login                         │
│  - auth:updateLocalUsername(): Allow username customization      │
├─────────────────────────────────────────────────────────────────┤
│  Frontend Auth Flow:                                              │
│  - On app init: Check isElectron()                               │
│  - If no authenticated user + isElectron: Use guest user        │
│  - If no authenticated user + !isElectron: Show login prompt    │
├─────────────────────────────────────────────────────────────────┤
│  Sync Flow (after login):                                         │
│  - Upload: Check login → check permission → upload               │
│  - Download: Check login → fetch permitted tournaments → save    │
│  - Guest tournaments become owned by authenticated user          │
└─────────────────────────────────────────────────────────────────┘
```

## Tournament Edit Permission Logic

A user can edit a tournament if:
1. They are an Admin, OR
2. They are the creator (`created_by`), OR
3. They are in the tournament's `schedulers` list

```
def can_edit_tournament(user, tournament):
    if user.role == 'ADMIN':
        return True
    if tournament.created_by == user:
        return True
    if user in tournament.schedulers.all():
        return True
    return False
```

## API Endpoints

### Authentication
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/login/` | Session login | No |
| POST | `/api/auth/logout/` | Session logout | No |
| GET | `/api/auth/me/` | Current user info | No |

### User Management (Admin Only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/` | List all users |
| POST | `/api/users/` | Create user |
| GET | `/api/users/{id}/` | Get user details |
| PUT | `/api/users/{id}/` | Update user |
| DELETE | `/api/users/{id}/` | Delete user |

### Tournament Scheduler Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tournaments/{id}/add_scheduler/` | Add scheduler (admin/creator) |
| POST | `/api/tournaments/{id}/remove_scheduler/` | Remove scheduler (admin/creator) |

## Database Schema

### User Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254),
    role VARCHAR(20) DEFAULT 'SCHEDULER',
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Tournament Extensions
```sql
ALTER TABLE tournament ADD COLUMN created_by_id UUID REFERENCES users(id);
CREATE TABLE tournament_schedulers (
    tournament_id UUID REFERENCES tournament(id),
    user_id UUID REFERENCES users(id),
    PRIMARY KEY (tournament_id, user_id)
);
```

## Session-based Authentication

The system uses Django's session authentication with CSRF protection:

1. **Login**: POST `/api/auth/login/` with credentials
2. **Session Cookie**: Django sets sessionid cookie
3. **CSRF Token**: Frontend reads from cookie, sends in X-CSRFToken header
4. **Logout**: POST `/api/auth/logout/` clears session

## Migration Plan

### Default Admin User
A data migration creates the default admin user:
- Username: `admin`
- Password: `admin`
- Role: `ADMIN`

### Existing Tournament Data
- `created_by` field allows NULL for existing tournaments
- `schedulers` M2M field starts empty

## Future Enhancements

1. **Self-registration**: Allow schedulers/guests to create accounts
2. **Fencer/Referee roles**: Additional roles with tournament-specific permissions
3. **Password reset**: Email-based password recovery
4. **API tokens**: For desktop app persistent authentication
5. **Two-factor authentication**: Enhanced security for admins