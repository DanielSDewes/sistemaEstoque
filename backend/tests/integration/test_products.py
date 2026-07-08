"""Integration tests for product CRUD, search and stock computation."""
import uuid


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:6]}"


def test_create_and_get_product(client, admin_headers):
    code = _unique("P")
    resp = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={"internal_code": code, "name": "Produto Teste", "min_stock": 5},
    )
    assert resp.status_code == 201, resp.text
    pid = resp.json()["id"]
    assert resp.json()["stock"]["current"] == 0

    got = client.get(f"/api/v1/products/{pid}", headers=admin_headers)
    assert got.status_code == 200
    assert got.json()["internal_code"] == code


def test_duplicate_internal_code_conflicts(client, admin_headers):
    code = _unique("DUP")
    payload = {"internal_code": code, "name": "Dup"}
    assert client.post("/api/v1/products", headers=admin_headers, json=payload).status_code == 201
    resp = client.post("/api/v1/products", headers=admin_headers, json=payload)
    assert resp.status_code == 409


def test_search_by_name(client, admin_headers):
    name = _unique("Buscavel")
    client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={"internal_code": _unique("S"), "name": name},
    )
    resp = client.get(f"/api/v1/products?q={name}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_update_product_is_audited(client, admin_headers):
    pid = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={"internal_code": _unique("UPD"), "name": "Antigo"},
    ).json()["id"]
    resp = client.put(
        f"/api/v1/products/{pid}", headers=admin_headers, json={"name": "Novo Nome"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Novo Nome"

    audit = client.get(
        "/api/v1/audit?entity=Product&action=alteracao", headers=admin_headers
    ).json()
    assert audit["total"] >= 1
