"""Integration test for the full inventory lifecycle with auto-adjustment."""
import uuid


def _seed_product_with_stock(client, headers, qty: int) -> int:
    pid = client.post(
        "/api/v1/products",
        headers=headers,
        json={"internal_code": f"INV-{uuid.uuid4().hex[:6]}", "name": "Inv Produto"},
    ).json()["id"]
    client.post(
        "/api/v1/movements",
        headers=headers,
        json={"product_id": pid, "movement_type": "compra", "quantity": qty},
    )
    return pid


def test_inventory_generates_adjustment_on_approval(client, admin_headers):
    pid = _seed_product_with_stock(client, admin_headers, 100)

    code = f"INV-{uuid.uuid4().hex[:6]}"
    inv = client.post(
        "/api/v1/inventories",
        headers=admin_headers,
        json={"code": code, "scope": "todo_estoque"},
    ).json()
    item = next(i for i in inv["items"] if i["product_id"] == pid)
    assert item["system_quantity"] == 100

    # Count 90 -> shortage of 10
    counted = client.patch(
        f"/api/v1/inventories/{inv['id']}/items/{item['id']}",
        headers=admin_headers,
        json={"counted_quantity": 90},
    ).json()
    counted_item = next(i for i in counted["items"] if i["product_id"] == pid)
    assert counted_item["difference"] == -10

    summary = client.get(
        f"/api/v1/inventories/{inv['id']}/summary", headers=admin_headers
    ).json()
    assert summary["shortage_qty"] >= 10

    client.post(f"/api/v1/inventories/{inv['id']}/finish", headers=admin_headers)
    approved = client.post(
        f"/api/v1/inventories/{inv['id']}/approve", headers=admin_headers
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "aprovado"

    # Stock reconciled to the counted value via a generated movement.
    stock = client.get(f"/api/v1/products/{pid}", headers=admin_headers).json()["stock"]
    assert stock["current"] == 90


def test_cannot_approve_before_finish(client, admin_headers):
    _seed_product_with_stock(client, admin_headers, 10)
    code = f"INV-{uuid.uuid4().hex[:6]}"
    inv = client.post(
        "/api/v1/inventories",
        headers=admin_headers,
        json={"code": code, "scope": "todo_estoque"},
    ).json()
    resp = client.post(f"/api/v1/inventories/{inv['id']}/approve", headers=admin_headers)
    assert resp.status_code == 400
