"""FastAPI application entrypoint with centralized error handling."""
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
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.observability import metrics_payload, record_request, setup_sentry

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201
    configure_logging("DEBUG" if settings.DEBUG else "INFO")
    setup_sentry()
    logger.info("Starting %s (%s)", settings.PROJECT_NAME, settings.ENVIRONMENT)
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "API REST do Sistema de Gestao de Estoque. "
        "Arquitetura em camadas (Controller -> Service -> Repository)."
    ),
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
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


@app.middleware("http")
async def request_logger(request: Request, call_next):  # noqa: ANN001, ANN201
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Request-ID"] = request_id

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
def metrics() -> Response:
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
