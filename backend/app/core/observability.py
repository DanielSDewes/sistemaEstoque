"""Observability: Prometheus metrics and optional Sentry error tracking.

Both integrations are optional: if the libraries are not installed or not
configured, the helpers degrade to no-ops so the app still runs.
"""
import logging

from app.core.config import settings

logger = logging.getLogger("app.observability")

try:  # pragma: no cover - optional dependency
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Histogram,
        generate_latest,
    )

    _PROM = True
    REQUEST_COUNT = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
    )
    REQUEST_LATENCY = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency (seconds)",
        ["method", "path"],
    )
except Exception:  # pragma: no cover
    _PROM = False
    CONTENT_TYPE_LATEST = "text/plain"


def metrics_enabled() -> bool:
    return _PROM and settings.ENABLE_METRICS


def record_request(method: str, path: str, status: int, duration_s: float) -> None:
    if not metrics_enabled():
        return
    REQUEST_COUNT.labels(method=method, path=path, status=str(status)).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(duration_s)


def metrics_payload() -> tuple[bytes, str]:
    if not metrics_enabled():
        return b"# metrics disabled\n", CONTENT_TYPE_LATEST
    return generate_latest(), CONTENT_TYPE_LATEST


def setup_sentry() -> None:
    if not settings.SENTRY_DSN:
        return
    try:  # pragma: no cover - optional dependency
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1,
        )
        logger.info("Sentry initialized")
    except Exception as exc:  # pragma: no cover
        logger.warning("Sentry init failed: %s", exc)
