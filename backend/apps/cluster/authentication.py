from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


class ClusterProxyAuthentication(BaseAuthentication):
    """
    Authenticate proxied requests from follower nodes.

    When a follower proxies a write request to the master, it includes
    X-Cluster-Proxy: follower and X-Cluster-User: <username> headers.
    This authentication class looks up the user by username and
    authenticates the request as that user.

    Only used when X-Cluster-Proxy header is present. Must be registered
    BEFORE SessionAuthentication in DEFAULT_AUTHENTICATION_CLASSES so
    that proxied requests are authenticated without requiring a session.
    """

    def authenticate(self, request):
        if request.META.get("HTTP_X_CLUSTER_PROXY") != "follower":
            return None

        username = request.META.get("HTTP_X_CLUSTER_USER")
        if not username:
            raise AuthenticationFailed("Cluster proxy request missing X-Cluster-User header")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise AuthenticationFailed(f"Cluster proxy user '{username}' not found on this node")

        return (user, None)

    def authenticate_header(self, request):
        return "ClusterProxy"
