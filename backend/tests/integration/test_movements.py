"""Integration tests for movement-driven stock and its business rules."""
import uuid

import pytest


def _new_product(client, headers, **overrides) -> int:
    payload = {"internal_code": f"M-{uuid.uuid4().hex[:6]}", "name": "Mov Produto"}
    payload.update(overrides)
    return client.post("/api/v1/products", headers=headers, json=payload).json()["id"]


def test_stock_is_derived_from_movements(client, admin_headers):
    pid = _new_product(client, admin_headers)
    client.post(
        "/api/v1/movements",
        headers=admin_headers,
        json={"product_id": pid, "movement_type": "compra", "quantity": 50},
    )
    client.post(
        "/api/v1/movements",
        headers=admin_headers,
        json={"product_id": pid, "movement_type": "venda", "quantity": 20},
    )
    stock = client.get(f"/api/v1/products/{pid}", headers=admin_headers).json()["stock"]
    assert stock["current"] == 30


def test_negative_stock_blocked(client, admin_headers):
    pid = _new_product(client, admin_headers)
    resp = client.post(
        "/api/v1/movements",
        headers=admin_headers,
        json={"product_id": pid, "movement_type": "venda", "quantity": 1},
    )
    assert resp.status_code == 400
    assert "insuficiente" in resp.json()["detail"].lower()


def test_inactive_product_cannot_move(client, admin_headers):
    pid = _new_product(client, admin_headers, is_active=False)
    resp = client.post(
        "/api/v1/movements",
        headers=admin_headers,
        json={"product_id": pid, "movement_type": "compra", "quantity": 10},
    )
    assert resp.status_code == 400
    assert "inativ" in resp.json()["detail"].lower()


def test_cancel_movement_preserves_history_and_reverses_balance(client, admin_headers):
    pid = _new_product(client, admin_headers)
    mid = client.post(
        "/api/v1/movements",
        headers=admin_headers,
        json={"product_id": pid, "movement_type": "compra", "quantity": 40},
    ).json()["id"]
    assert client.get(f"/api/v1/products/{pid}", headers=admin_headers).json()["stock"]["current"] == 40

    resp = client.post(
        f"/api/v1/movements/{mid}/cancel",
        headers=admin_headers,
        json={"reason": "Erro de digitacao"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_cancelled"] is True

    # Balance reversed, but the movement still exists in history.
    assert client.get(f"/api/v1/products/{pid}", headers=admin_headers).json()["stock"]["current"] == 0
    history = client.get(f"/api/v1/products/{pid}/history", headers=admin_headers).json()
    assert history["total"] == 1


@pytest.mark.parametrize("mtype,direction", [("compra", "entrada"), ("venda", "saida")])
def test_movement_direction_is_derived(client, admin_headers, mtype, direction):
    pid = _new_product(client, admin_headers)
    if direction == "saida":
        client.post(
            "/api/v1/movements",
            headers=admin_headers,
            json={"product_id": pid, "movement_type": "compra", "quantity": 100},
        )
    resp = client.post(
        "/api/v1/movements",
        headers=admin_headers,
        json={"product_id": pid, "movement_type": mtype, "quantity": 5},
    )
    assert resp.json()["direction"] == direction
