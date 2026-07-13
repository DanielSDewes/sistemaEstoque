"""Helpers for resolving the real client IP behind (or without) a proxy.

``X-Forwarded-For`` is client-controllable, so it is only honored when the app
is explicitly configured to sit behind a trusted proxy that sets it. Otherwise
the direct socket peer (``request.client.host``) is used, which cannot be
spoofed. This keeps IP-based rate limiting and audit logs trustworthy.
"""
from fastapi import Request

from app.core.config import settings


def client_ip(request: Request) -> str | None:
    """Return the best-effort client IP, respecting proxy configuration.

    XFF format is ``client, proxy1, proxy2`` where each proxy appends the peer
    it received the request from. With ``N`` trusted proxies in front of us the
    real client is the ``N``-th entry counted from the right.
    """
    peer = request.client.host if request.client else None
    if not settings.TRUST_PROXY_HEADERS:
        return peer

    forwarded = request.headers.get("x-forwarded-for")
    if not forwarded:
        return peer

    parts = [p.strip() for p in forwarded.split(",") if p.strip()]
    if not parts:
        return peer

    hops = max(1, settings.TRUSTED_PROXY_HOPS)
    # Clamp: if the chain is shorter than the configured hop count, fall back to
    # the left-most (original) entry rather than indexing out of range.
    index = len(parts) - hops
    return parts[index] if index >= 0 else parts[0]
