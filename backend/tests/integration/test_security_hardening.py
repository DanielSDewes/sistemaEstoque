"""Integration tests for auth hardening: revocation, rotation, lockout, policy."""
import uuid


def _new_user(client, admin_headers, username: str, password: str = "Strong@123") -> int:
    role = next(
        r for r in client.get("/api/v1/roles", headers=admin_headers).json()["items"]
        if r["name"] == "Operador"
    )
    resp = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "full_name": "Test User",
            "email": f"{username}@estoque.com",
            "username": username,
            "password": password,
            "role_id": role["id"],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_logout_revokes_access_token(client, admin_headers):
    username = f"logout_{uuid.uuid4().hex[:6]}"
    _new_user(client, admin_headers, username)
    token = client.post(
        "/api/v1/auth/login", data={"username": username, "password": "Strong@123"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    client.post("/api/v1/auth/logout", headers=headers)
    # Token is now revoked.
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_refresh_rotation_rejects_reuse(client, admin_headers):
    username = f"refresh_{uuid.uuid4().hex[:6]}"
    _new_user(client, admin_headers, username)
    login = client.post(
        "/api/v1/auth/login", data={"username": username, "password": "Strong@123"}
    ).json()
    refresh = login["refresh_token"]

    first = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert first.status_code == 200
    # Reusing the rotated refresh token is rejected.
    second = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert second.status_code == 401


def test_account_lockout_after_failed_attempts(client, admin_headers):
    username = f"lock_{uuid.uuid4().hex[:6]}"
    _new_user(client, admin_headers, username)
    for _ in range(5):
        client.post("/api/v1/auth/login", data={"username": username, "password": "Wrong@123"})
    # Even the correct password is now blocked by lockout.
    resp = client.post(
        "/api/v1/auth/login", data={"username": username, "password": "Strong@123"}
    )
    assert resp.status_code == 401
    assert "bloquead" in resp.json()["detail"].lower()


def test_weak_password_rejected(client, admin_headers):
    role = next(
        r for r in client.get("/api/v1/roles", headers=admin_headers).json()["items"]
        if r["name"] == "Operador"
    )
    resp = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "full_name": "Weak",
            "email": "weakpw@estoque.com",
            "username": "weakpw",
            "password": "weak",
            "role_id": role["id"],
        },
    )
    assert resp.status_code == 422
