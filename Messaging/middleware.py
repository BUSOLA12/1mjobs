from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def get_user_from_token(token):
    """Validate a SimpleJWT access token and return the matching user.

    Returns AnonymousUser for any missing/invalid/expired token so the
    consumer can reject unauthenticated connections.
    """
    User = get_user_model()
    try:
        access = AccessToken(token)  # raises TokenError if invalid/expired
        user_id = access.get("user_id")
        if user_id is None:
            return AnonymousUser()
        return User.objects.get(id=user_id)
    except (TokenError, KeyError, User.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Authenticate WebSocket connections from a `token` query-string param.

    WebSocket handshakes can't carry an Authorization header, and the access
    token isn't stored in a cookie (only the path-scoped refresh token is), so
    the short-lived access token is passed as a query param and validated here.
    The resulting user is placed on the scope; the consumer derives identity
    from `scope['user']` rather than trusting a client-supplied user id.
    """

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token = query.get("token", [None])[0]
        scope["user"] = await get_user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)
