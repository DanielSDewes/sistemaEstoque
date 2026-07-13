"""Application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic import PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "CHANGE-ME-in-production-with-a-long-random-string"


class Settings(BaseSettings):
    """Central application settings, populated from env / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # --- Application ---
    PROJECT_NAME: str = "Sistema de Gestao de Estoque"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # --- Security / JWT ---
    SECRET_KEY: str = DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8h
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- Database ---
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "estoque"
    POSTGRES_PASSWORD: str = "estoque"
    POSTGRES_DB: str = "estoque"
    DATABASE_URL: str | None = None

    # --- CORS (comma-separated string; parsed by the ``cors_origins`` property) ---
    # Kept as a plain str so pydantic-settings does not attempt to JSON-decode it
    # when supplied via env vars / .env (which would raise a SettingsError).
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # --- Business rules (configurable) ---
    ALLOW_NEGATIVE_STOCK: bool = False
    EXPIRY_ALERT_DAYS: int = 30  # alert window for near-expiry products

    # --- Auth hardening ---
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15
    LOGIN_RATE_LIMIT_MAX: int = 10  # requests per window per IP+user
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # --- Reverse proxy / client IP resolution ---
    # Only trust X-Forwarded-For when the app is deployed behind a proxy that
    # sets it. TRUSTED_PROXY_HOPS is the number of trusted proxies between the
    # client and the app (used to pick the real client IP from the XFF chain).
    TRUST_PROXY_HEADERS: bool = False
    TRUSTED_PROXY_HOPS: int = 1

    # --- Rate limiting backend ---
    # When set, the login rate limiter uses Redis so the limit is shared across
    # workers/instances; otherwise it falls back to an in-process window.
    REDIS_URL: str | None = None

    # --- Observability ---
    SENTRY_DSN: str | None = None
    ENABLE_METRICS: bool = True
    # When set, /metrics requires this token (Bearer header or ?token=). In
    # production with no token configured, /metrics is hidden entirely.
    METRICS_TOKEN: str | None = None

    # --- Frontend / e-mail (password reset links) ---
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "no-reply@estoque.local"
    SMTP_TLS: bool = True

    # --- Uploads ---
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 5

    # --- Seed / bootstrap admin ---
    FIRST_ADMIN_EMAIL: str = "admin@estoque.com"
    FIRST_ADMIN_PASSWORD: str = "Admin@123"
    FIRST_ADMIN_NAME: str = "Administrador"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}

    @model_validator(mode="after")
    def _enforce_prod_secret(self) -> "Settings":
        """Refuse to boot in production with the insecure default secret key."""
        if self.is_production and self.SECRET_KEY == DEFAULT_SECRET_KEY:
            raise ValueError(
                "SECRET_KEY must be set to a strong, unique value when "
                "ENVIRONMENT=production."
            )
        return self

    @property
    def cors_origins(self) -> list[str]:
        """CORS origins parsed from the comma-separated configuration string."""
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def sqlalchemy_database_uri(self) -> str:
        """Return the effective DB URI, preferring an explicit DATABASE_URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg2",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor so the env is parsed only once."""
    return Settings()


settings = get_settings()
