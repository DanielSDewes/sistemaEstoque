"""Integration tests for the password reset flow."""
import time


def _create_user(client, admin_headers, username, email, password="Initial@123"):
    role_id = client.get("/api/v1/roles", headers=admin_headers).json()["items"][0]["id"]
    resp = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "full_name": "Reset User",
            "email": email,
            "username": username,
            "password": password,
            "role_id": role_id,
        },
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


def test_forgot_and_reset_password(client, admin_headers):
    email = "resetme@estoque.com"
    _create_user(client, admin_headers, "resetme", email)

    resp = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert resp.status_code == 200, resp.text
    token = resp.json()["reset_token"]
    assert token  # surfaced outside production

    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "BrandNew@123"},
    )
    assert resp.status_code == 200, resp.text

    # Old password rejected, new password accepted.
    assert client.post(
        "/api/v1/auth/login", data={"username": "resetme", "password": "Initial@123"}
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login", data={"username": "resetme", "password": "BrandNew@123"}
    ).status_code == 200

    # The token is single-use.
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "Another@123"},
    )
    assert resp.status_code == 422


def test_reset_rejects_weak_password(client, admin_headers):
    email = "weakreset@estoque.com"
    _create_user(client, admin_headers, "weakreset", email)
    token = client.post(
        "/api/v1/auth/forgot-password", json={"email": email}
    ).json()["reset_token"]
    resp = client.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": "weak"}
    )
    assert resp.status_code == 422


def test_forgot_unknown_email_still_succeeds(client):
    resp = client.post(
        "/api/v1/auth/forgot-password", json={"email": "ghost@nowhere.com"}
    )
    assert resp.status_code == 200
    assert resp.json()["reset_token"] is None


def test_password_reset_invalidates_existing_sessions(client, admin_headers):
    email = "sessionkill@estoque.com"
    _create_user(client, admin_headers, "sessionkill", email)

    token = client.post(
        "/api/v1/auth/login", data={"username": "sessionkill", "password": "Initial@123"}
    ).json()["access_token"]
    old_headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/auth/me", headers=old_headers).status_code == 200

    # Ensure the reset lands more than the 1s leeway after the token's iat.
    time.sleep(1.5)
    reset_token = client.post(
        "/api/v1/auth/forgot-password", json={"email": email}
    ).json()["reset_token"]
    client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "Rotated@123"},
    )

    # The previously-issued access token is now rejected.
    assert client.get("/api/v1/auth/me", headers=old_headers).status_code == 401
