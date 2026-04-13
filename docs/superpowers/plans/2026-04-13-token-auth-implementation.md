# Token-Based Authentication Implementation Plan

> **For agentic workers:** Execute task-by-task using checkbox (`- [ ]`) syntax.

**Goal:** Replace session-cookie authentication with JWT token-based authentication for both web and desktop apps.

**Architecture:** 
- Backend generates JWT on login, frontend stores in localStorage
- Frontend sends `Authorization: Bearer <token>` header with all API requests
- Backend validates token and sets `request.user` from token claims
- No cookies needed, works from any origin (file://, http://localhost, etc.)

**Tech Stack:** PyJWT (for JWT), Django REST Framework, Vue 3, TypeScript

---

## Task 1: Backend - Install PyJWT dependency

**Files:**
- Create: `backend/requirements.txt` (add PyJWT if not present)

- [ ] **Step 1: Check if PyJWT is already installed**

Run: `grep -i pyjwt backend/requirements.txt`
Expected: empty (not installed) or version number

- [ ] **Step 2: Add PyJWT to requirements.txt**

If not found, add `PyJWT>=2.8.0` to `backend/requirements.txt`

---

## Task 2: Backend - Create JWT utilities module

**Files:**
- Create: `backend/apps/users/jwt_auth.py`

- [ ] **Step 1: Create jwt_auth.py**

```python
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from django.conf import settings


def get_token_expiration() -> datetime:
    """Get token expiration time."""
    days = getattr(settings, 'JWT_EXPIRATION_DAYS', 7)
    return datetime.now(timezone.utc) + timedelta(days=days)


def create_token(user) -> str:
    """
    Create a JWT token for the given user.
    
    Args:
        user: User model instance
        
    Returns:
        JWT token string
    """
    payload = {
        'user_id': str(user.id),
        'username': user.username,
        'role': user.role,
        'exp': get_token_expiration(),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm='HS256'
    )


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload dict or None if invalid/expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user_id from token."""
    payload = decode_token(token)
    if payload:
        return payload.get('user_id')
    return None
```

- [ ] **Step 2: Run Python to verify module loads**

Run: `cd backend && python -c "from apps.users.jwt_auth import create_token, decode_token; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add backend/apps/users/jwt_auth.py
git commit -m "feat: add JWT utilities module"
```

---

## Task 3: Backend - Add get_token method to User model

**Files:**
- Modify: `backend/apps/users/models.py`

- [ ] **Step 1: Add get_token method to User model**

Add after line 31:
```python
    def get_token(self) -> str:
        """Generate JWT token for this user."""
        from .jwt_auth import create_token
        return create_token(self)
```

- [ ] **Step 2: Verify User model loads**

Run: `cd backend && python -c "from apps.users.models import User; u = User(username='test'); print('get_token' in dir(u))"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add backend/apps/users/models.py
git commit -m "feat: add get_token method to User model"
```

---

## Task 4: Backend - Update AuthViewSet login to return token

**Files:**
- Modify: `backend/apps/users/views.py`

- [ ] **Step 1: Update login action to return token**

Replace the login action (lines 16-28):
```python
    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=username, password=password)
        if user:
            token = user.get_token()
            return Response({
                "user": UserSerializer(user).data,
                "token": token
            })
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
```

- [ ] **Step 2: Update logout action (stateless JWT - just return success)**

Replace the logout action (lines 30-34):
```python
    @action(detail=False, methods=["post"])
    def logout(self, request):
        return Response({"success": True})
```

- [ ] **Step 3: Verify views load**

Run: `cd backend && python -c "from apps.users.views import AuthViewSet; print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add backend/apps/users/views.py
git commit -m "feat: update login to return JWT token"
```

---

## Task 5: Backend - Create JWTAuthentication class

**Files:**
- Modify: `backend/apps/fencing_organizer/authentication.py`

- [ ] **Step 1: Add JWTAuthentication class**

Add after line 12:
```python


class JWTAuthentication(BaseAuthentication):
    """
    JWT token authentication for API requests.
    
    Expects Authorization header: Bearer <token>
    """

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header[7:]  # Strip 'Bearer ' prefix
        if not token:
            return None

        from backend.apps.users.jwt_auth import decode_token, get_user_id_from_token
        from backend.apps.users.models import User

        user_id = get_user_id_from_token(token)
        if not user_id:
            return None

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer'
```

- [ ] **Step 2: Verify authentication class loads**

Run: `cd backend && python -c "from apps.fencing_organizer.authentication import JWTAuthentication; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add backend/apps/fencing_organizer/authentication.py
git commit -m "feat: add JWTAuthentication class"
```

---

## Task 6: Backend - Update REST framework settings for JWT auth

**Files:**
- Modify: `backend/PisteMaster/settings/base.py`

- [ ] **Step 1: Add JWT settings after REST_FRAMEWORK config**

Add after line 114 (after REST_FRAMEWORK closing brace):
```python
# JWT Configuration
JWT_EXPIRATION_DAYS = 7
```

- [ ] **Step 2: Update DEFAULT_AUTHENTICATION_CLASSES**

Modify lines 93-97 to include JWTAuthentication:
```python
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "backend.apps.cluster.authentication.ClusterProxyAuthentication",
        "backend.apps.fencing_organizer.authentication.JWTAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
```

- [ ] **Step 3: Verify settings load**

Run: `cd backend && python -c "from django.conf import settings; print('JWT_EXPIRATION_DAYS:', settings.JWT_EXPIRATION_DAYS)"`
Expected: JWT_EXPIRATION_DAYS: 7

- [ ] **Step 4: Commit**

```bash
git add backend/PisteMaster/settings/base.py
git commit -m "feat: add JWT to REST framework authentication classes"
```

---

## Task 7: Frontend - Create auth storage utility

**Files:**
- Create: `web_frontend/src/services/authStorage.ts`

- [ ] **Step 1: Create authStorage.ts**

```typescript
const AUTH_TOKEN_KEY = 'auth_token'

export function getToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token)
}

export function removeToken(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY)
}
```

- [ ] **Step 2: Commit**

```bash
git add web_frontend/src/services/authStorage.ts
git commit -m "feat: add auth token storage utility"
```

---

## Task 8: Frontend - Update authService to use tokens

**Files:**
- Modify: `web_frontend/src/services/authService.ts`

- [ ] **Step 1: Replace authService.ts content**

```typescript
import type { User } from '@/types/user'
import { getApiBaseUrl } from './api'
import { getToken, setToken, removeToken } from './authStorage'

export const AuthService = {
  async login(username: string, password: string): Promise<User> {
    const response = await fetch(`${await getApiBaseUrl()}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.error || 'Login failed')
    }

    const data = await response.json()
    if (data.token) {
      setToken(data.token)
    }
    return data.user
  },

  async loginAsGuest(): Promise<User> {
    return this.login('Guest', 'Guest')
  },

  async logout(): Promise<void> {
    removeToken()
  },

  async getCurrentUser(): Promise<User | null> {
    const token = getToken()
    if (!token) {
      return null
    }

    try {
      const response = await fetch(`${await getApiBaseUrl()}/auth/me/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        removeToken()
        return null
      }

      const data = await response.json()
      return data.user
    } catch {
      removeToken()
      return null
    }
  },

  getToken(): string | null {
    return getToken()
  },
}
```

- [ ] **Step 2: Commit**

```bash
git add web_frontend/src/services/authService.ts
git commit -m "feat: update authService to use JWT tokens"
```

---

## Task 9: Frontend - Update api.ts to expose getAuthHeaders

**Files:**
- Modify: `web_frontend/src/services/api.ts`

- [ ] **Step 1: Update api.ts to export getAuthHeaders**

```typescript
import { isElectron } from '@/utils/platform'
import { getToken } from './authStorage'

let apiUrlCache: string | null = null

export async function getApiBaseUrl(): Promise<string> {
  if (apiUrlCache) {
    return apiUrlCache
  }

  if (isElectron()) {
    try {
      const electron = window.electron as unknown as { cluster: { getApiUrl: () => Promise<string> } }
      const url = await electron.cluster.getApiUrl()
      apiUrlCache = url
      return url
    } catch (_error) {
      console.warn('Failed to get API URL from Electron, falling back to env')
    }
  }

  const envUrl = (import.meta.env.VITE_API_BASE_URL as string) || '/api'
  apiUrlCache = envUrl
  return apiUrlCache
}

export async function getAuthHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export const API_BASE_URL = '/api'
```

- [ ] **Step 2: Commit**

```bash
git add web_frontend/src/services/api.ts
git commit -m "feat: add getAuthHeaders for token auth"
```

---

## Task 10: Frontend - Update DataManager to use auth headers

**Files:**
- Modify: `web_frontend/src/services/DataManager.ts`

- [ ] **Step 1: Update DataManager imports and getHeaders function**

Replace the import and getHeaders function (lines 1-16):
```typescript
import {IndexedDBService} from './storage/IndexedDBService';
import {ElMessage} from 'element-plus';
import {getAuthHeaders} from './api';
```

Replace the getHeaders function with:
```typescript
async function getHeaders(): Promise<Record<string, string>> {
    return getAuthHeaders()
}
```

- [ ] **Step 2: Update all fetch calls to use await getHeaders()**

This is a replaceAll operation on `${API_BASE_URL}/` → needs to use `${await getApiBaseUrl()}/` AND use `await getHeaders()`.

The pattern is:
- Replace `getHeaders()` with `await getHeaders()`
- The URL still uses `await getApiBaseUrl()` which was updated in a previous task

This step requires careful find-replace in the file. All fetch calls should:
1. Use `await getHeaders()` instead of `getHeaders()`
2. The URL pattern remains `${await getApiBaseUrl()}/...`

- [ ] **Step 3: Commit**

```bash
git add web_frontend/src/services/DataManager.ts
git commit -m "feat: update DataManager to use auth headers"
```

---

## Task 11: Frontend - Update ClusterService to use auth headers

**Files:**
- Modify: `web_frontend/src/services/cluster/ClusterService.ts`

- [ ] **Step 1: Import getAuthHeaders**

Add to imports:
```typescript
import { getApiBaseUrl, getAuthHeaders } from '../api'
```

- [ ] **Step 2: Update healthCheck to use auth headers**

Replace:
```typescript
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${await getApiBaseUrl()}/cluster/status/health/`)
      return response.ok
    } catch {
      return false
    }
  }
```

With:
```typescript
  async healthCheck(): Promise<boolean> {
    try {
      const headers = await getAuthHeaders()
      const response = await fetch(`${await getApiBaseUrl()}/cluster/status/health/`, { headers })
      return response.ok
    } catch {
      return false
    }
  }
```

- [ ] **Step 3: Commit**

```bash
git add web_frontend/src/services/cluster/ClusterService.ts
git commit -m "feat: update ClusterService to use auth headers"
```

---

## Task 12: Verify and test

**Files:**
- Test: Full integration test

- [ ] **Step 1: Run lint on all changed files**

Run: `cd web_frontend && npm run lint`
Expected: 0 errors

- [ ] **Step 2: Run backend tests**

Run: `cd backend && python manage.py test apps.users.tests`
Expected: Tests pass

- [ ] **Step 3: Commit all remaining changes**

```bash
git add -A && git commit -m "feat: complete token-based auth implementation"
```

---

## Task 13: Push and create PR

- [ ] **Step 1: Push to remote**

```bash
git push
```

- [ ] **Step 2: Create PR if needed**

```bash
gh pr create --title "feat: token-based authentication" --body "Replaces session-cookie auth with JWT tokens for desktop and web apps."
```
