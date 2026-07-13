"""FastAPI application entrypoint with centralized error handling."""
import hmac
import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError, AuthenticationError, NotFoundError
from app.core.logging import configure_logging
from app.core.observability import metrics_payload, record_request, setup_sentry

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201
    configure_logging("DEBUG" if settings.DEBUG else "INFO")
    setup_sentry()
    logger.info("Starting %s (%s)", settings.PROJECT_NAME, settings.ENVIRONMENT)
    # Best-effort cleanup of expired revoked-token rows so the denylist stays
    # small. Defensive: never let a maintenance step block startup.
    try:
        from app.core.database import SessionLocal
        from app.services.token_revocation import purge_expired

        with SessionLocal() as db:
            removed = purge_expired(db)
            if removed:
                logger.info("Purged %s expired revoked token(s)", removed)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Token denylist purge skipped: %s", exc)
    yield
    logger.info("Shutting down")


# Swagger/ReDoc expose the full API surface; disable them in production.
_docs_enabled = not settings.is_production
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "API REST do Sistema de Gestao de Estoque. "
        "Arquitetura em camadas (Controller -> Service -> Repository)."
    ),
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if _docs_enabled else None,
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded product photos.
_upload_root = Path(settings.UPLOAD_DIR)
_upload_root.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_upload_root)), name="uploads")


def _apply_security_headers(request: Request, response: Response) -> None:
    """Baseline security headers on every backend response.

    nginx sets these for the SPA; adding them here protects the API, uploads and
    docs when the backend is reached directly (e.g. its own URL on a PaaS).
    """
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    # Swagger/ReDoc need to load their own assets/inline scripts; a strict CSP
    # would break them, so skip the docs routes (disabled in prod anyway).
    path = request.url.path
    if not (path.startswith("/docs") or path.startswith("/redoc")):
        response.headers.setdefault(
            "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
        )
    if settings.is_production:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )


@app.middleware("http")
async def request_logger(request: Request, call_next):  # noqa: ANN001, ANN201
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Request-ID"] = request_id
    _apply_security_headers(request, response)

    # Use the route template (not the raw path) to keep metric cardinality low.
    route = request.scope.get("route")
    path_label = getattr(route, "path", request.url.path)
    record_request(request.method, path_label, response.status_code, elapsed)

    logger.info(
        "request",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": round(elapsed * 1000, 2),
        },
    )
    return response


# --- Centralized exception handlers ---
@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "detail": exc.message, "details": exc.details},
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": "ValidationError", "detail": "Dados invalidos", "details": exc.errors()},
    )


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": "InternalServerError", "detail": "Erro interno do servidor"},
    )


@app.get("/health", tags=["Infra"], summary="Liveness check")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/metrics", tags=["Infra"], summary="Prometheus metrics", include_in_schema=False)
def metrics(request: Request) -> Response:
    token = settings.METRICS_TOKEN
    if token:
        auth = request.headers.get("authorization", "")
        provided = (
            auth[7:] if auth.lower().startswith("bearer ")
            else request.query_params.get("token", "")
        )
        if not hmac.compare_digest(provided, token):
            raise AuthenticationError("Token de metricas invalido")
    elif settings.is_production:
        # No token configured in production: do not expose metrics at all.
        raise NotFoundError()
    payload, content_type = metrics_payload()
    return Response(content=payload, media_type=content_type)


@app.get("/health/ready", tags=["Infra"], summary="Readiness check (verifies DB)")
def readiness() -> JSONResponse:
    from sqlalchemy import text

    from app.core.database import SessionLocal

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return JSONResponse(status_code=200, content={"status": "ready"})
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Readiness check failed: %s", exc)
        return JSONResponse(status_code=503, content={"status": "unavailable"})


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
