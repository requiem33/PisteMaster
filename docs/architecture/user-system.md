# User System Architecture

## Overview

PisteMaster implements a role-based access control (RBAC) system with three user roles for the MVP release.

## User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access: create/edit/delete all tournaments, manage users (CRUD), assign schedulers, use distributed cluster |
| **Scheduler** | Create tournaments, edit tournaments where assigned (creator or in schedulers list) |
| **Guest** | Create and edit own tournaments (desktop app only), cannot manage users or use distributed cluster |

## Architecture

### Backend (Django)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Django Backend                            │
├─────────────────────────────────────────────────────────────────┤
│  Users App:                                                      │
│  - Custom User model (AbstractUser + role field)                 │
│  - Role choices: ADMIN, SCHEDULER, GUEST                          │
│  - AuthViewSet: login, logout, me endpoints                      │
│  - UserViewSet: CRUD for admin only                              │
│  - Data migration creates default Admin and Guest users            │
├─────────────────────────────────────────────────────────────────┤
│  Tournament Model Extensions:                                    │
│  - created_by: FK to User (tournament creator)                  │
│  - schedulers: M2M to User (users who can edit)                 │
├─────────────────────────────────────────────────────────────────┤
│  Permission Classes:                                              │
│  - IsAdmin: Admin only                                           │
│  - IsSchedulerOrAdmin: Scheduler or Admin for creation             │
│  - IsSchedulerOrAdminOrGuest: Guest can also create tournaments   │
│  - IsTournamentEditor: Object-level for edit permissions          │
│  - IsTournamentCreatorOrAdmin: Only creator/admin can manage schedulers │
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
│  - login(username, password): authenticate with backend          │
│  - loginAsGuest(): authenticate as Guest (desktop only)          │
│  - logout(): clear session                                       │
│  - fetchCurrentUser(): restore session on app load              │
├─────────────────────────────────────────────────────────────────┤
│  Auth Service:                                                    │
│  - login(username, password) → User                              │
│  - loginAsGuest() → User (calls login with Guest/Guest)          │
│  - logout() → void                                               │
│  - getCurrentUser() → User | null                               │
├─────────────────────────────────────────────────────────────────┤
│  Route Guards:                                                    │
│  - Web: Redirect unauthenticated users to /login                │
│  - Desktop: Auto-login as Guest if not authenticated            │
│  - Preserve redirect target in query params                      │
│  - Admin-only routes check                                       │
├─────────────────────────────────────────────────────────────────┤
│  Components:                                                      │
│  - Login.vue: Login form + "Continue as Guest" on desktop        │
│  - UserMenu.vue: Username + role tag (Admin/Scheduler/Guest)     │
└─────────────────────────────────────────────────────────────────┘
```

### Desktop App vs Web App Behavior

**Web App (Browser):**
- Unauthenticated users can only **browse** public tournaments (read-only)
- No guest user - must login to create/edit tournaments
- All write operations require authentication via Django backend
- User display: Shows username + role badge when logged in, "Login" button when not

**Desktop App (Electron):**
- App **auto-logins as Guest** on startup if no authenticated session
- Guest user can **create and edit own tournaments** in local SQLite database
- Guest tournaments stored with `created_by = Guest user`
- User display: Shows "Guest" + GUEST badge, with "Login" button available
- When user logs in: Guest tournaments can be synced to cloud later

```
┌─────────────────────────────────────────────────────────────────┐
│                      Electron Desktop App                         │
├─────────────────────────────────────────────────────────────────┤
│  Startup Flow:                                                    │
│  1. App loads Vue frontend                                       │
│  2. fetchCurrentUser() called                                    │
│  3. If no session + isElectron(): call loginAsGuest()            │
│  4. Guest session established with backend                       │
│  5. User can create/edit tournaments as Guest                     │
├─────────────────────────────────────────────────────────────────┤
│  Local SQLite Database (always available):                       │
│  - Guest user record created via data migration                   │
│  - Offline tournament creation with Guest user                   │
│  - Tournaments stored with created_by = Guest                     │
├─────────────────────────────────────────────────────────────────┤
│  Authentication:                                                   │
│  - POST /api/auth/login/ with Guest/Guest credentials            │
│  - Session-based auth (same as regular users)                     │
│  - Can logout and login with different account                   │
├─────────────────────────────────────────────────────────────────┤
│  Sync Flow (manual, future feature):                              │
│  - Upload: Login → check permission → upload local tournaments    │
│  - Guest tournaments transferred to authenticated user            │
└─────────────────────────────────────────────────────────────────┘
```

## Tournament Edit Permission Logic

A user can edit a tournament if:
1. They are an Admin, OR
2. They are the creator (`created_by`), OR
3. They are in the tournament's `schedulers` list (Schedulers only)

**Guest users**: Can only edit tournaments they created (cannot be added to schedulers list).

```
def can_edit_tournament(user, tournament):
    if user.role == 'ADMIN':
        return True
    if tournament.created_by == user:
        return True
    if user.role == 'SCHEDULER' and user in tournament.schedulers.all():
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

### Default Guest User (Desktop Only)
A data migration creates the default Guest user (runs for desktop settings):
- Username: `Guest`
- Password: `Guest`
- Role: `GUEST`

### Existing Tournament Data
- `created_by` field allows NULL for existing tournaments
- `schedulers` M2M field starts empty

## Future Enhancements

1. **Self-registration**: Allow schedulers/guests to create accounts
2. **Fencer/Referee roles**: Additional roles with tournament-specific permissions
3. **Password reset**: Email-based password recovery
4. **API tokens**: For desktop app persistent authentication
5. **Two-factor authentication**: Enhanced security for admins
6. **Cloud sync**: Upload local tournaments to cloud after login