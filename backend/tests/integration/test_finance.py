"""Integration tests for the financial module (accounts payable/receivable)."""
import uuid

API = "/api/v1"


def _customer(client, headers) -> int:
    resp = client.post(
        f"{API}/customers",
        headers=headers,
        json={"name": "Fin Cliente", "phone": "11999990000"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _supplier(client, headers) -> int:
    cnpj = f"{uuid.uuid4().int % 10**14:014d}"
    resp = client.post(
        f"{API}/suppliers",
        headers=headers,
        json={"legal_name": "Fin Fornecedor", "cnpj": cnpj},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _bank(client, headers, opening: float = 0) -> dict:
    resp = client.post(
        f"{API}/finance/bank-accounts",
        headers=headers,
        json={"name": f"Caixa {uuid.uuid4().hex[:4]}", "opening_balance": opening},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _receivable(client, headers, customer_id: int, total: float, first_due: str, count: int = 1) -> dict:
    resp = client.post(
        f"{API}/finance/accounts",
        headers=headers,
        json={
            "direction": "receber",
            "customer_id": customer_id,
            "document": f"FAT-{uuid.uuid4().hex[:5]}",
            "total_amount": total,
            "installment_plan": {"count": count, "first_due_date": first_due, "interval_days": 30},
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _settle(client, headers, installment_id: int, payload: dict) -> dict:
    resp = client.post(
        f"{API}/finance/installments/{installment_id}/settlements", headers=headers, json=payload
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# --- Creation / installments ---
def test_create_receivable_splits_into_installments(client, admin_headers):
    cid = _customer(client, admin_headers)
    acc = _receivable(client, admin_headers, cid, 1000, "2030-01-10", count=2)
    assert acc["status"] == "em_aberto"
    assert acc["total_amount"] == 1000
    assert len(acc["installments"]) == 2
    assert sum(i["original_amount"] for i in acc["installments"]) == 1000
    assert all(i["balance"] == 500 for i in acc["installments"])


def test_receivable_requires_customer(client, admin_headers):
    resp = client.post(
        f"{API}/finance/accounts",
        headers=admin_headers,
        json={
            "direction": "receber",
            "document": "X",
            "installments": [{"due_date": "2030-01-01", "amount": 100}],
        },
    )
    assert resp.status_code == 400
    assert "cliente" in resp.json()["detail"].lower()


def test_payable_requires_supplier(client, admin_headers):
    resp = client.post(
        f"{API}/finance/accounts",
        headers=admin_headers,
        json={
            "direction": "pagar",
            "document": "X",
            "installments": [{"due_date": "2030-01-01", "amount": 100}],
        },
    )
    assert resp.status_code == 400
    assert "fornecedor" in resp.json()["detail"].lower()


# --- Settlements (baixas) ---
def test_partial_then_full_settlement_transitions_status(client, admin_headers):
    cid = _customer(client, admin_headers)
    acc = _receivable(client, admin_headers, cid, 500, "2030-02-10")
    inst = acc["installments"][0]

    acc = _settle(client, admin_headers, inst["id"], {"amount": 200})
    inst = acc["installments"][0]
    assert acc["status"] == "parcial"
    assert inst["status"] == "parcial"
    assert inst["balance"] == 300

    acc = _settle(client, admin_headers, inst["id"], {"amount": 300})
    assert acc["status"] == "quitado"
    assert acc["installments"][0]["balance"] == 0


def test_settlement_with_bank_updates_balance(client, admin_headers):
    cid = _customer(client, admin_headers)
    bank = _bank(client, admin_headers, opening=100)
    acc = _receivable(client, admin_headers, cid, 400, "2030-03-10")
    inst = acc["installments"][0]

    _settle(client, admin_headers, inst["id"], {"amount": 400, "bank_account_id": bank["id"]})
    after = client.get(f"{API}/finance/bank-accounts/{bank['id']}", headers=admin_headers).json()
    assert after["current_balance"] == 500  # 100 opening + 400 received


def test_cancel_settlement_reverses_bank_and_status(client, admin_headers):
    cid = _customer(client, admin_headers)
    bank = _bank(client, admin_headers, opening=0)
    acc = _receivable(client, admin_headers, cid, 400, "2030-04-10")
    inst = acc["installments"][0]
    acc = _settle(client, admin_headers, inst["id"], {"amount": 400, "bank_account_id": bank["id"]})
    settlement_id = acc["installments"][0]["settlements"][0]["id"]

    resp = client.post(f"{API}/finance/settlements/{settlement_id}/cancel", headers=admin_headers)
    assert resp.status_code == 200
    acc = resp.json()
    assert acc["status"] == "em_aberto"
    assert acc["installments"][0]["balance"] == 400
    bank_after = client.get(f"{API}/finance/bank-accounts/{bank['id']}", headers=admin_headers).json()
    assert bank_after["current_balance"] == 0


def test_overdue_status_is_derived(client, admin_headers):
    cid = _customer(client, admin_headers)
    resp = client.post(
        f"{API}/finance/accounts",
        headers=admin_headers,
        json={
            "direction": "receber",
            "customer_id": cid,
            "document": "FAT-OLD",
            "installments": [{"due_date": "2020-01-01", "amount": 100}],
        },
    )
    assert resp.status_code == 201, resp.text
    acc = resp.json()
    assert acc["status"] == "vencido"
    assert acc["installments"][0]["status"] == "vencido"


def test_suggested_charges_for_overdue(client, admin_headers):
    cid = _customer(client, admin_headers)
    acc = client.post(
        f"{API}/finance/accounts",
        headers=admin_headers,
        json={
            "direction": "receber",
            "customer_id": cid,
            "installments": [{"due_date": "2020-01-01", "amount": 1000}],
        },
    ).json()
    iid = acc["installments"][0]["id"]
    resp = client.get(f"{API}/finance/installments/{iid}/suggested-charges", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["days_overdue"] > 0
    assert body["fine"] > 0  # 2% of balance


# --- Reports ---
def test_dashboard_and_cashflow(client, admin_headers):
    cid = _customer(client, admin_headers)
    bank = _bank(client, admin_headers, opening=0)
    acc = _receivable(client, admin_headers, cid, 600, "2030-05-10")
    inst = acc["installments"][0]
    _settle(client, admin_headers, inst["id"], {"amount": 600, "bank_account_id": bank["id"]})

    dash = client.get(f"{API}/finance/dashboard", headers=admin_headers).json()
    assert dash["received_today"] >= 600
    assert dash["cash_total"] >= 600

    cf = client.get(
        f"{API}/finance/cashflow",
        headers=admin_headers,
        params={"start": "2020-01-01", "end": "2031-12-31", "group_by": "month"},
    ).json()
    t = cf["totals"]
    assert abs(t["net_realized"] - (t["inflow_realized"] - t["outflow_realized"])) < 0.01
    assert t["inflow_realized"] >= 600
