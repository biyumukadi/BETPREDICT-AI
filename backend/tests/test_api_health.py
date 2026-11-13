"""API smoke tests using SQLite in-memory where possible."""

import os

# Force sqlite for isolated tests before app import side effects
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("PRIMARY_DATA_PROVIDER", "demo")
os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+aiosqlite:///:memory:",
)
os.environ.setdefault("DATABASE_URL_SYNC", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")

from fastapi.testclient import TestClient

from app.main import create_app


def test_health():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True


def test_openapi_available():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/v1/openapi.json")
    assert resp.status_code == 200
    assert "openapi" in resp.json()


def test_plans_public():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/v1/subscriptions/plans")
    assert resp.status_code == 200
    plans = {p["plan"] for p in resp.json()}
    assert plans == {"free", "premium", "pro"}
