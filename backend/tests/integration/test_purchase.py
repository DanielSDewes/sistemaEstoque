"""Integration tests for the purchase order (compras) flow."""
import itertools

_cnpj_seq = itertools.count(1)


def _make_supplier(client, headers, name):
    cnpj = f"{next(_cnpj_seq):014d}"  # unique 14-digit document per supplier
    resp = client.post(
        "/api/v1/suppliers", headers=headers, json={"legal_name": name, "cnpj": cnpj}
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["id"]


def _make_product(client, headers, code, name="Produto Compra"):
    resp = client.post(
        "/api/v1/products", headers=headers, json={"internal_code": code, "name": name}
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["id"]


def test_full_receive_updates_stock_and_cost(client, admin_headers):
    supplier_id = _make_supplier(client, admin_headers, "Fornecedor OC Full")
    product_id = _make_product(client, admin_headers, "OC-FULL-1")

    resp = client.post(
        "/api/v1/purchase-orders",
        headers=admin_headers,
        json={
            "supplier_id": supplier_id,
            "items": [{"product_id": product_id, "quantity": 10, "unit_cost": 5.0}],
        },
    )
    assert resp.status_code == 201, resp.text
    po = resp.json()
    assert po["status"] == "rascunho"
    assert po["number"].startswith("OC-")
    assert po["total_amount"] == 50.0
    po_id = po["id"]

    resp = client.post(f"/api/v1/purchase-orders/{po_id}/place", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "emitido"

    resp = client.post(
        f"/api/v1/purchase-orders/{po_id}/receive", headers=admin_headers, json={}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "recebido"
    assert body["received_at"] is not None
    assert body["items"][0]["received_quantity"] == 10.0
    assert body["items"][0]["pending_quantity"] == 0.0

    # Stock cost is derived from the receipt (weighted moving average).
    prod = client.get(f"/api/v1/products/{product_id}", headers=admin_headers).json()
    assert prod["average_cost"] == 5.0

    hist = client.get(
        f"/api/v1/products/{product_id}/history", headers=admin_headers
    ).json()
    assert any(m["movement_type"] == "compra" for m in hist["items"])


def test_partial_then_complete(client, admin_headers):
    supplier_id = _make_supplier(client, admin_headers, "Fornecedor OC Partial")
    product_id = _make_product(client, admin_headers, "OC-PART-1")
    po_id = client.post(
        "/api/v1/purchase-orders",
        headers=admin_headers,
        json={
            "supplier_id": supplier_id,
            "items": [{"product_id": product_id, "quantity": 10, "unit_cost": 2.0}],
        },
    ).json()["id"]
    client.post(f"/api/v1/purchase-orders/{po_id}/place", headers=admin_headers)

    item_id = client.get(
        f"/api/v1/purchase-orders/{po_id}", headers=admin_headers
    ).json()["items"][0]["id"]
    resp = client.post(
        f"/api/v1/purchase-orders/{po_id}/receive",
        headers=admin_headers,
        json={"items": [{"item_id": item_id, "quantity": 4}]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "parcial"
    assert body["items"][0]["received_quantity"] == 4.0
    assert body["items"][0]["pending_quantity"] == 6.0

    # A partially-received order cannot be cancelled.
    resp = client.post(
        f"/api/v1/purchase-orders/{po_id}/cancel",
        headers=admin_headers,
        json={"reason": "mudou de ideia"},
    )
    assert resp.status_code == 400

    resp = client.post(
        f"/api/v1/purchase-orders/{po_id}/receive", headers=admin_headers, json={}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "recebido"


def test_over_receive_is_rejected(client, admin_headers):
    supplier_id = _make_supplier(client, admin_headers, "Fornecedor OC Over")
    product_id = _make_product(client, admin_headers, "OC-OVER-1")
    po_id = client.post(
        "/api/v1/purchase-orders",
        headers=admin_headers,
        json={
            "supplier_id": supplier_id,
            "items": [{"product_id": product_id, "quantity": 3, "unit_cost": 1.0}],
        },
    ).json()["id"]
    client.post(f"/api/v1/purchase-orders/{po_id}/place", headers=admin_headers)
    item_id = client.get(
        f"/api/v1/purchase-orders/{po_id}", headers=admin_headers
    ).json()["items"][0]["id"]
    resp = client.post(
        f"/api/v1/purchase-orders/{po_id}/receive",
        headers=admin_headers,
        json={"items": [{"item_id": item_id, "quantity": 5}]},
    )
    assert resp.status_code == 400


def test_draft_can_be_placed_only_once(client, admin_headers):
    supplier_id = _make_supplier(client, admin_headers, "Fornecedor OC Place")
    product_id = _make_product(client, admin_headers, "OC-PLACE-1")
    po_id = client.post(
        "/api/v1/purchase-orders",
        headers=admin_headers,
        json={
            "supplier_id": supplier_id,
            "items": [{"product_id": product_id, "quantity": 1, "unit_cost": 1.0}],
        },
    ).json()["id"]
    assert client.post(
        f"/api/v1/purchase-orders/{po_id}/place", headers=admin_headers
    ).status_code == 200
    # Placing again is a business-rule error.
    assert client.post(
        f"/api/v1/purchase-orders/{po_id}/place", headers=admin_headers
    ).status_code == 400
