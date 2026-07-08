"""Integration tests for authentication and RBAC guards."""


def test_login_success(client):
    resp = client.post("/api/v1/auth/login", data={"username": "admin", "password": "Admin@123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "admin@estoque.com"


def test_login_wrong_password(client):
    resp = client.post("/api/v1/auth/login", data={"username": "admin", "password": "nope"})
    assert resp.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_with_token(client, admin_headers):
    resp = client.get("/api/v1/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"


def test_protected_endpoint_without_permission_is_denied(client, admin_headers):
    # Create a read-only user and confirm it cannot create products.
    roles = client.get("/api/v1/roles", headers=admin_headers).json()["items"]
    read_only = next(r for r in roles if r["name"] == "Somente Consulta")
    client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "full_name": "Consulta User",
            "email": "consulta@estoque.com",
            "username": "consulta",
            "password": "Consulta@123",
            "role_id": read_only["id"],
        },
    )
    token = client.post(
        "/api/v1/auth/login", data={"username": "consulta", "password": "Consulta@123"}
    ).json()["access_token"]
    ro_headers = {"Authorization": f"Bearer {token}"}

    # Allowed: view products
    assert client.get("/api/v1/products", headers=ro_headers).status_code == 200
    # Denied: create product
    resp = client.post(
        "/api/v1/products",
        headers=ro_headers,
        json={"internal_code": "RO-1", "name": "Blocked"},
    )
    assert resp.status_code == 403
