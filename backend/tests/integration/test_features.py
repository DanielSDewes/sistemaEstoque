"""Integration tests for avg cost, per-location stock, alerts and CSV import."""
import uuid


def _u(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:6]}"


def _new_product(client, headers, **overrides) -> dict:
    payload = {"internal_code": _u("F"), "name": "Feature Produto"}
    payload.update(overrides)
    return client.post("/api/v1/products", headers=headers, json=payload).json()


def test_weighted_average_cost(client, admin_headers):
    pid = _new_product(client, admin_headers)["id"]
    client.post(
        "/api/v1/movements",
        headers=admin_headers,
        json={"product_id": pid, "movement_type": "compra", "quantity": 100, "unit_cost": 10},
    )
    client.post(
        "/api/v1/movements",
        headers=admin_headers,
        json={"product_id": pid, "movement_type": "compra", "quantity": 100, "unit_cost": 20},
    )
    product = client.get(f"/api/v1/products/{pid}", headers=admin_headers).json()
    # (100*10 + 100*20) / 200 = 15
    assert abs(product["average_cost"] - 15.0) < 0.001


def test_per_location_stock(client, admin_headers):
    corridor = client.post(
        "/api/v1/corridors", headers=admin_headers, json={"code": _u("C"), "name": "Corredor F"}
    ).json()
    shelf = client.post(
        "/api/v1/shelves",
        headers=admin_headers,
        json={"code": _u("S"), "name": "Prateleira F", "corridor_id": corridor["id"]},
    ).json()
    pid = _new_product(client, admin_headers)["id"]
    client.post(
        "/api/v1/product-locations",
        headers=admin_headers,
        json={"product_id": pid, "corridor_id": corridor["id"], "shelf_id": shelf["id"]},
    )
    client.post(
        "/api/v1/movements",
        headers=admin_headers,
        json={
            "product_id": pid,
            "movement_type": "compra",
            "quantity": 40,
            "destination_location_id": shelf["id"],
        },
    )
    locations = client.get(f"/api/v1/products/{pid}/locations", headers=admin_headers).json()
    loc = next(loc for loc in locations if loc["shelf_id"] == shelf["id"])
    assert loc["stock_balance"] == 40


def test_alerts_below_minimum(client, admin_headers):
    pid = _new_product(client, admin_headers, min_stock=100)["id"]
    below = client.get("/api/v1/alerts/below-minimum", headers=admin_headers).json()
    assert any(item["product_id"] == pid for item in below)
    summary = client.get("/api/v1/alerts/summary", headers=admin_headers).json()
    assert summary["below_minimum_count"] >= 1


def test_csv_import_upsert(client, admin_headers):
    code = _u("CSV").replace("-", "")
    csv = f"internal_code,name,unit,min_stock\n{code},Importado A,UN,15\n".encode()
    first = client.post(
        "/api/v1/products/import",
        headers=admin_headers,
        files={"file": ("p.csv", csv, "text/csv")},
    )
    assert first.status_code == 200
    assert first.json()["created"] == 1

    # Re-importing the same code updates instead of duplicating.
    second = client.post(
        "/api/v1/products/import",
        headers=admin_headers,
        files={"file": ("p.csv", csv, "text/csv")},
    )
    assert second.json()["updated"] == 1
    assert second.json()["created"] == 0
