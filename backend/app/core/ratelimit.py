"""Sliding-window rate limiter with an optional Redis backend.

By default this uses an in-process window, which is correct only within a
single process. When ``REDIS_URL`` is configured the limiter uses Redis so the
window is shared across all workers/instances. If Redis is configured but
unreachable, it degrades gracefully to the in-process limiter (fail-open on the
backend, never on the limit itself) so authentication keeps working.
"""
import logging
import threading
import time
import uuid
from collections import defaultdict, deque

from app.core.config import settings

logger = logging.getLogger("app.ratelimit")

_WINDOWS: dict[str, deque[float]] = defaultdict(deque)
_LOCK = threading.Lock()

# Lazily-initialized Redis client. ``False`` means "tried and unavailable".
_redis_client: object | None = None


def _in_memory_limited(key: str, max_events: int, window_seconds: int) -> bool:
    now = time.monotonic()
    cutoff = now - window_seconds
    with _LOCK:
        events = _WINDOWS[key]
        while events and events[0] < cutoff:
            events.popleft()
        if len(events) >= max_events:
            return True
        events.append(now)
        return False


def _get_redis():
    """Return a connected Redis client, or ``None`` if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client or None
    if not settings.REDIS_URL:
        _redis_client = False
        return None
    try:
        import redis  # optional dependency

        client = redis.Redis.from_url(
            settings.REDIS_URL, socket_timeout=0.25, socket_connect_timeout=0.25
        )
        client.ping()
        _redis_client = client
        logger.info("Rate limiter using Redis backend")
        return client
    except Exception as exc:  # pragma: no cover - depends on external service
        logger.warning("Redis unavailable, falling back to in-memory limiter: %s", exc)
        _redis_client = False
        return None


def _redis_limited(client, key: str, max_events: int, window_seconds: int) -> bool:
    now = time.time()
    cutoff = now - window_seconds
    rkey = f"ratelimit:{key}"
    try:
        pipe = client.pipeline()
        pipe.zremrangebyscore(rkey, 0, cutoff)
        pipe.zcard(rkey)
        count = pipe.execute()[1]
        if count >= max_events:
            return True
        pipe = client.pipeline()
        pipe.zadd(rkey, {f"{now}-{uuid.uuid4().hex}": now})
        pipe.expire(rkey, window_seconds)
        pipe.execute()
        return False
    except Exception as exc:  # pragma: no cover - depends on external service
        logger.warning("Redis limiter error, using in-memory fallback: %s", exc)
        return _in_memory_limited(key, max_events, window_seconds)


def is_rate_limited(key: str, max_events: int, window_seconds: int) -> bool:
    """Record an event for ``key`` and return True if it exceeds the limit."""
    client = _get_redis()
    if client is not None:
        return _redis_limited(client, key, max_events, window_seconds)
    return _in_memory_limited(key, max_events, window_seconds)


def reset(key: str) -> None:
    with _LOCK:
        _WINDOWS.pop(key, None)
    client = _get_redis()
    if client is not None:
        try:
            client.delete(f"ratelimit:{key}")
        except Exception:  # pragma: no cover - best effort
            pass
