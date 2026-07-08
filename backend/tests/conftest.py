"""Shared pytest fixtures: isolated SQLite DB, seeded data and auth client."""
import os

# Point the whole app at an isolated SQLite file BEFORE importing app modules.
os.environ["DATABASE_URL"] = "sqlite:///./test_estoque.db"
os.environ["ALLOW_NEGATIVE_STOCK"] = "false"
# Effectively disable login rate limiting for the shared test session
# (the limiter itself is unit-tested directly).
os.environ["LOGIN_RATE_LIMIT_MAX"] = "100000"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.db.init_db import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        init_db(db)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_estoque.db"):
        try:
            os.remove("test_estoque.db")
        except OSError:
            pass


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def admin_headers(client: TestClient) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login", data={"username": "admin", "password": "Admin@123"}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
