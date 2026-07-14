from slowapi import Limiter

from app.core.config import settings
from app.core.security import verify_token


def _rate_limit_key(request):
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = verify_token(auth[7:])
            user_id = payload.get("id")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    return f"ip:{request.client.host if request.client else 'unknown'}"


limiter = Limiter(
    key_func=_rate_limit_key,
    storage_uri=settings.REDIS_URL,
    storage_options={"socket_connect_timeout": 2, "socket_timeout": 2},
    strategy="moving-window",
)


def rate_limit(max_requests: int, window_seconds: int):
    """Rate limit decorator.
    Usage: @rate_limit(20, 900)
    """
    return limiter.limit(f"{max_requests}/{window_seconds}seconds")
