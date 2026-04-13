from rest_framework.authentication import BaseAuthentication, SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication without CSRF enforcement.
    Used for API-only backends where the frontend is on a different origin.
    CSRF protection is handled by CORS and SameSite cookie settings.
    """

    def enforce_csrf(self, request):
        return None


class JWTAuthentication(BaseAuthentication):
    """
    JWT token authentication for API requests.

    Expects Authorization header: Bearer <token>
    """

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Strip 'Bearer ' prefix
        if not token:
            return None

        from backend.apps.users.jwt_auth import get_user_id_from_token
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
        return "Bearer"
