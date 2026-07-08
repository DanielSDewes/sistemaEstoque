"""Integration tests for the CRM: customers, orders and sales history."""
import uuid

API = "/api/v1"


def _new_product(client, headers, **overrides) -> int:
    payload = {"internal_code": f"C-{uuid.uuid4().hex[:6]}", "name": "CRM Produto"}
    payload.update(overrides)
    return client.post(f"{API}/products", headers=headers, json=payload).json()["id"]


def _stock_product(client, headers, qty: int, **overrides) -> int:
    pid = _new_product(client, headers, **overrides)
    client.post(
        f"{API}/movements",
        headers=headers,
        json={"product_id": pid, "movement_type": "compra", "quantity": qty},
    )
    return pid


def _stock(client, headers, pid: int) -> float:
    return client.get(f"{API}/products/{pid}", headers=headers).json()["stock"]["current"]


def _new_customer(client, headers, **overrides) -> dict:
    payload = {"name": "Cliente Teste", "phone": "(11) 99999-0000"}
    payload.update(overrides)
    resp = client.post(f"{API}/customers", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


# --- Customers ---
def test_customer_requires_only_name_and_phone(client, admin_headers):
    resp = client.post(
        f"{API}/customers",
        headers=admin_headers,
        json={"name": "Fulano", "phone": "11988887777"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "Fulano"
    assert body["addresses"] == []


def test_customer_missing_phone_is_rejected(client, admin_headers):
    resp = client.post(f"{API}/customers", headers=admin_headers, json={"name": "Sem Fone"})
    assert resp.status_code == 422


def test_customer_with_multiple_addresses_marks_one_primary(client, admin_headers):
    customer = _new_customer(
        client,
        admin_headers,
        name="Multi Endereco",
        addresses=[
            {"label": "Casa", "city": "Sao Paulo", "state": "SP"},
            {"label": "Trabalho", "city": "Campinas", "state": "SP"},
        ],
    )
    assert len(customer["addresses"]) == 2
    primaries = [a for a in customer["addresses"] if a["is_primary"]]
    assert len(primaries) == 1  # first is auto-marked primary


def test_customer_search_by_name(client, admin_headers):
    _new_customer(client, admin_headers, name="Beltrano Buscavel", phone="11955554444")
    resp = client.get(f"{API}/customers", headers=admin_headers, params={"q": "Buscavel"})
    assert resp.status_code == 200
    assert any(c["name"] == "Beltrano Buscavel" for c in resp.json()["items"])


# --- Orders ---
def test_order_draft_does_not_touch_stock(client, admin_headers):
    pid = _stock_product(client, admin_headers, 100)
    customer = _new_customer(client, admin_headers)
    resp = client.post(
        f"{API}/orders",
        headers=admin_headers,
        json={
            "customer_id": customer["id"],
            "items": [{"product_id": pid, "quantity": 10, "unit_price": 9.5}],
        },
    )
    assert resp.status_code == 201, resp.text
    order = resp.json()
    assert order["status"] == "rascunho"
    assert order["number"].startswith("PED-")
    assert order["total_amount"] == 95.0
    assert _stock(client, admin_headers, pid) == 100  # untouched while draft


def test_confirm_order_deducts_stock(client, admin_headers):
    pid = _stock_product(client, admin_headers, 100)
    customer = _new_customer(client, admin_headers)
    order = client.post(
        f"{API}/orders",
        headers=admin_headers,
        json={
            "customer_id": customer["id"],
            "items": [{"product_id": pid, "quantity": 30, "unit_price": 5}],
        },
    ).json()

    resp = client.post(f"{API}/orders/{order['id']}/confirm", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "confirmado"
    assert _stock(client, admin_headers, pid) == 70


def test_confirm_is_atomic_when_one_item_lacks_stock(client, admin_headers):
    ok_pid = _stock_product(client, admin_headers, 50)
    empty_pid = _new_product(client, admin_headers)  # zero stock
    customer = _new_customer(client, admin_headers)
    order = client.post(
        f"{API}/orders",
        headers=admin_headers,
        json={
            "customer_id": customer["id"],
            "items": [
                {"product_id": ok_pid, "quantity": 5, "unit_price": 1},
                {"product_id": empty_pid, "quantity": 1, "unit_price": 1},
            ],
        },
    ).json()

    resp = client.post(f"{API}/orders/{order['id']}/confirm", headers=admin_headers)
    assert resp.status_code == 400
    # Nothing deducted, order still a draft (no partial movement).
    assert _stock(client, admin_headers, ok_pid) == 50
    assert client.get(f"{API}/orders/{order['id']}", headers=admin_headers).json()["status"] == "rascunho"


def test_cancel_confirmed_order_restores_stock(client, admin_headers):
    pid = _stock_product(client, admin_headers, 100)
    customer = _new_customer(client, admin_headers)
    order = client.post(
        f"{API}/orders",
        headers=admin_headers,
        json={
            "customer_id": customer["id"],
            "items": [{"product_id": pid, "quantity": 40, "unit_price": 2}],
        },
    ).json()
    client.post(f"{API}/orders/{order['id']}/confirm", headers=admin_headers)
    assert _stock(client, admin_headers, pid) == 60

    resp = client.post(
        f"{API}/orders/{order['id']}/cancel",
        headers=admin_headers,
        json={"reason": "Cliente desistiu"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelado"
    assert _stock(client, admin_headers, pid) == 100  # restored


def test_customer_sales_history_lists_orders(client, admin_headers):
    pid = _stock_product(client, admin_headers, 100)
    customer = _new_customer(client, admin_headers)
    order = client.post(
        f"{API}/orders",
        headers=admin_headers,
        json={
            "customer_id": customer["id"],
            "items": [{"product_id": pid, "quantity": 3, "unit_price": 10}],
        },
    ).json()
    client.post(f"{API}/orders/{order['id']}/confirm", headers=admin_headers)

    resp = client.get(f"{API}/customers/{customer['id']}/orders", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["number"] == order["number"]
    assert body["items"][0]["items"][0]["product_id"] == pid


def test_product_sale_price_persists(client, admin_headers):
    pid = _new_product(client, admin_headers, sale_price=19.9)
    body = client.get(f"{API}/products/{pid}", headers=admin_headers).json()
    assert body["sale_price"] == 19.9


def test_order_profit_accounts_for_cost_and_extra(client, admin_headers):
    pid = _new_product(client, admin_headers)
    # Purchase 100 @ cost 4.00 sets the product's average cost to 4.00.
    client.post(
        f"{API}/movements",
        headers=admin_headers,
        json={"product_id": pid, "movement_type": "compra", "quantity": 100, "unit_cost": 4},
    )
    customer = _new_customer(client, admin_headers)
    order = client.post(
        f"{API}/orders",
        headers=admin_headers,
        json={
            "customer_id": customer["id"],
            "extra_cost": 10,
            "items": [{"product_id": pid, "quantity": 5, "unit_price": 10}],
        },
    ).json()
    # Draft already estimates cost (5 * 4) and profit (50 - 20 - 10).
    assert order["extra_cost"] == 10.0
    assert order["total_amount"] == 50.0
    assert order["total_cost"] == 20.0
    assert order["profit"] == 20.0
    assert order["items"][0]["unit_cost"] == 4.0

    confirmed = client.post(f"{API}/orders/{order['id']}/confirm", headers=admin_headers).json()
    assert confirmed["profit"] == 20.0


def test_profit_report_is_internally_consistent(client, admin_headers):
    pid = _new_product(client, admin_headers)
    client.post(
        f"{API}/movements",
        headers=admin_headers,
        json={"product_id": pid, "movement_type": "compra", "quantity": 100, "unit_cost": 2},
    )
    customer = _new_customer(client, admin_headers)
    order = client.post(
        f"{API}/orders",
        headers=admin_headers,
        json={
            "customer_id": customer["id"],
            "extra_cost": 5,
            "items": [{"product_id": pid, "quantity": 10, "unit_price": 7}],
        },
    ).json()
    client.post(f"{API}/orders/{order['id']}/confirm", headers=admin_headers)

    resp = client.get(f"{API}/orders/reports/profit", headers=admin_headers, params={"group_by": "month"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["periods"], "deve haver ao menos um periodo"
    t = data["totals"]
    # profit == revenue - cost - extra, and this order contributes 10*(7-2)-5 = 45.
    assert abs(t["profit"] - (t["revenue"] - t["cost"] - t["extra_cost"])) < 0.01
    assert t["profit"] >= 45.0


def test_cannot_delete_customer_with_orders(client, admin_headers):
    pid = _stock_product(client, admin_headers, 10)
    customer = _new_customer(client, admin_headers)
    client.post(
        f"{API}/orders",
        headers=admin_headers,
        json={
            "customer_id": customer["id"],
            "items": [{"product_id": pid, "quantity": 1, "unit_price": 1}],
        },
    )
    resp = client.delete(f"{API}/customers/{customer['id']}", headers=admin_headers)
    assert resp.status_code == 400
    assert "pedido" in resp.json()["detail"].lower()
