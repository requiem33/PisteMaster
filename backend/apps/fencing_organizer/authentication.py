from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication without CSRF enforcement.
    Used for API-only backends where the frontend is on a different origin.
    CSRF protection is handled by CORS and SameSite cookie settings.
    """

    def enforce_csrf(self, request):
        return None
