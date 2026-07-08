"""Lightweight in-process sliding-window rate limiter (dependency-free).

Suitable for single-instance or per-instance limiting. For multi-instance
deployments, back this with Redis; the interface can stay the same.
"""
import threading
import time
from collections import defaultdict, deque

_WINDOWS: dict[str, deque[float]] = defaultdict(deque)
_LOCK = threading.Lock()


def is_rate_limited(key: str, max_events: int, window_seconds: int) -> bool:
    """Record an event for ``key`` and return True if it exceeds the limit."""
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


def reset(key: str) -> None:
    with _LOCK:
        _WINDOWS.pop(key, None)
