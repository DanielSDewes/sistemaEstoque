"""Gunicorn configuration for production (uvicorn workers)."""
import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
# Default to (2*CPU)+1, overridable via WEB_CONCURRENCY.
workers = int(os.getenv("WEB_CONCURRENCY", str(multiprocessing.cpu_count() * 2 + 1)))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
graceful_timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
