# Token-Based Authentication Design

**Date:** 2026-04-13  
**Status:** Approved

## Overview

Replace session-cookie authentication with JWT (JSON Web Token) based authentication to support:
- Desktop app (Electron) where frontend is served from `file://` origin
- Web app (development and production)
- Cluster mode where follower nodes proxy to master

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ AuthService │───▶│ localStorage│◀───│ HTTP Interceptor │ │
│  │  login()    │    │  (token)    │    │  (adds Bearer)   │ │
│  │  logout()   │    └─────────────┘    └─────────────┘    │
│  └─────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                              │ JWT in Authorization header
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ /api/auth/  │───▶│ JWT Middleware│───▶│ View/Service │    │
│  │   login     │    │  (validates) │    │             │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## JWT Token Structure

```json
{
  "user_id": "uuid",
  "username": "admin",
  "role": "ADMIN",
  "exp": 1752500000
}
```

**Settings:**
- Algorithm: HS256
- Expiration: 7 days
- Secret: Django's SECRET_KEY

## Components

### Backend

| File | Action | Description |
|------|--------|-------------|
| `apps/users/jwt_auth.py` | Create | JWT encode/decode utilities |
| `apps/users/views.py` | Modify | Login returns `{user, token}`, logout clears nothing (stateless) |
| `apps/fencing_organizer/authentication.py` | Modify | Add `JWTAuthentication` class |
| `apps/users/models.py` | Modify | Add `get_token()` method to User model |
| `PisteMaster/settings/base.py` | Modify | Add JWT config constants |

### Frontend

| File | Action | Description |
|------|--------|-------------|
| `services/authService.ts` | Modify | Store token in localStorage, send Authorization header |
| `services/api.ts` | Modify | Expose `getAuthHeaders()` using stored token |
| `stores/authStore.ts` | Modify | Store user + token |
| `utils/csrf.ts` | Modify | Remove or deprecate (CSRF not needed with tokens) |

## Data Flow

### Login
1. Frontend sends username/password to `/api/auth/login/`
2. Backend validates credentials, returns `{user, token}`
3. Frontend stores token in `localStorage.setItem('auth_token', token)`
4. Frontend sets user in auth state

### API Calls
1. Frontend includes `Authorization: Bearer <token>` header
2. Backend `JWTAuthentication` validates token
3. If valid, `request.user` is set from token claims
4. If invalid/expired, return 401

### Logout
1. Frontend clears token from `localStorage`
2. Frontend clears user from auth state
3. Backend: no action needed (stateless JWT)

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Token expired | Return 401, frontend clears token, redirect to login |
| Invalid token | Return 401, frontend clears token |
| No token provided | Return 401 |
| Invalid credentials | Return 401 with error message |

## Backward Compatibility

- Guest login: continues to work, same flow
- Cluster sync: uses existing session-based auth between nodes (no change needed)
- Web app dev (Vite proxy): tokens work across proxy since Authorization header is forwarded

## Security Considerations

- JWT stored in localStorage (XSS vulnerable, but acceptable for desktop app)
- Tokens expire in 7 days
- No token refresh (simplification)
- HTTPS required in production (tokens in headers)

## Testing

### Backend
- Unit tests for JWT encode/decode
- Unit tests for JWTAuthentication middleware
- Integration test for login endpoint

### Frontend
- Mock auth service in tests
- Verify token storage/retrieval
- Integration test for full login/logout flow
