# --- Backend image: FastAPI + Uvicorn on Python 3.12 ---
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# curl for the container healthcheck. psycopg2-binary ships a wheel, so no
# build toolchain is required.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN chmod +x ./entrypoint.sh

# Run as a non-root user.
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health/ready || exit 1

ENTRYPOINT ["./entrypoint.sh"]
# Production server: Gunicorn managing Uvicorn workers.
CMD ["gunicorn", "app.main:app", "-c", "gunicorn_conf.py"]
