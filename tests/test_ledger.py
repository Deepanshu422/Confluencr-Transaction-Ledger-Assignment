from decimal import Decimal


def test_create_account_starts_with_zero_balance(client):
    res = client.post("/api/v1/accounts", json={"name": "Alice"})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Alice"
    assert Decimal(str(data["balance"])) == Decimal("0.0000")


def test_create_account_rejects_client_provided_balance(client):
    # Requirement: The client should not be allowed to set the initial balance
    res = client.post("/api/v1/accounts", json={"name": "Bob", "balance": 500.0})
    assert res.status_code == 422


def test_credit_increases_balance(client):
    acc = client.post("/api/v1/accounts", json={"name": "Charlie"}).json()
    acc_id = acc["id"]

    tx = client.post(
        f"/api/v1/accounts/{acc_id}/transactions",
        json={
            "type": "credit",
            "amount": 100.50,
            "description": "Salary",
            "reference_id": "ref-charlie-001",
        },
    )
    assert tx.status_code == 201

    bal = client.get(f"/api/v1/accounts/{acc_id}/balance").json()
    assert Decimal(str(bal["balance"])) == Decimal("100.5000")


def test_debit_decreases_balance(client):
    acc = client.post("/api/v1/accounts", json={"name": "David"}).json()
    acc_id = acc["id"]

    client.post(
        f"/api/v1/accounts/{acc_id}/transactions",
        json={"type": "credit", "amount": 200.0, "reference_id": "ref-d-credit"},
    )
    tx = client.post(
        f"/api/v1/accounts/{acc_id}/transactions",
        json={"type": "debit", "amount": 60.0, "reference_id": "ref-d-debit"},
    )
    assert tx.status_code == 201

    bal = client.get(f"/api/v1/accounts/{acc_id}/balance").json()
    assert Decimal(str(bal["balance"])) == Decimal("140.0000")


def test_debit_fails_on_insufficient_balance(client):
    acc = client.post("/api/v1/accounts", json={"name": "Eve"}).json()
    acc_id = acc["id"]

    tx = client.post(
        f"/api/v1/accounts/{acc_id}/transactions",
        json={"type": "debit", "amount": 50.0, "reference_id": "ref-e-fail"},
    )
    assert tx.status_code == 400
    assert tx.json()["code"] == "INSUFFICIENT_FUNDS"

    bal = client.get(f"/api/v1/accounts/{acc_id}/balance").json()
    assert Decimal(str(bal["balance"])) == Decimal("0.0000")


def test_duplicate_reference_id_rejected(client):
    acc = client.post("/api/v1/accounts", json={"name": "Frank"}).json()
    acc_id = acc["id"]

    # First transaction succeeds
    res1 = client.post(
        f"/api/v1/accounts/{acc_id}/transactions",
        json={"type": "credit", "amount": 100.0, "reference_id": "dup-check-1"},
    )
    assert res1.status_code == 201

    # Identical reference_id on same account returns 409 Conflict
    res2 = client.post(
        f"/api/v1/accounts/{acc_id}/transactions",
        json={"type": "credit", "amount": 100.0, "reference_id": "dup-check-1"},
    )
    assert res2.status_code == 409
    assert res2.json()["code"] == "DUPLICATE_TRANSACTION"

    # Balance must remain unchanged (100, not 200)
    bal = client.get(f"/api/v1/accounts/{acc_id}/balance").json()
    assert Decimal(str(bal["balance"])) == Decimal("100.0000")


def test_same_reference_id_allowed_across_different_accounts(client):
    acc1 = client.post("/api/v1/accounts", json={"name": "Grace"}).json()["id"]
    acc2 = client.post("/api/v1/accounts", json={"name": "Heidi"}).json()["id"]

    res1 = client.post(
        f"/api/v1/accounts/{acc1}/transactions",
        json={"type": "credit", "amount": 50.0, "reference_id": "shared-ref-1"},
    )
    res2 = client.post(
        f"/api/v1/accounts/{acc2}/transactions",
        json={"type": "credit", "amount": 50.0, "reference_id": "shared-ref-1"},
    )
    assert res1.status_code == 201
    assert res2.status_code == 201


def test_transaction_history_pagination_and_sorting(client):
    acc_id = client.post("/api/v1/accounts", json={"name": "Ivan"}).json()["id"]

    # Insert 3 transactions
    for i in range(1, 4):
        client.post(
            f"/api/v1/accounts/{acc_id}/transactions",
            json={"type": "credit", "amount": 10.0 * i, "reference_id": f"page-ref-{i}"},
        )

    # Fetch page 1 with limit 2
    res = client.get(f"/api/v1/accounts/{acc_id}/transactions?page=1&limit=2")
    assert res.status_code == 200
    body = res.json()

    assert body["current_page"] == 1
    assert body["page_size"] == 2
    assert body["total_records"] == 3
    assert body["total_pages"] == 2
    assert len(body["data"]) == 2

    # Latest-first check: the last inserted transaction (page-ref-3) comes first
    assert body["data"][0]["reference_id"] == "page-ref-3"


def test_atomic_transfer_between_accounts(client):
    acc_a = client.post("/api/v1/accounts", json={"name": "Transferer A"}).json()["id"]
    acc_b = client.post("/api/v1/accounts", json={"name": "Receiver B"}).json()["id"]

    # Fund A with 100
    client.post(
        f"/api/v1/accounts/{acc_a}/transactions",
        json={"type": "credit", "amount": 100.0, "reference_id": "seed-a"},
    )

    # Transfer 40 from A to B
    res = client.post(
        "/api/v1/transfers",
        json={
            "source_account_id": acc_a,
            "destination_account_id": acc_b,
            "amount": 40.0,
            "description": "P2P Payment",
            "reference_id": "transfer-001",
        },
    )
    assert res.status_code == 200

    bal_a = client.get(f"/api/v1/accounts/{acc_a}/balance").json()
    bal_b = client.get(f"/api/v1/accounts/{acc_b}/balance").json()

    assert Decimal(str(bal_a["balance"])) == Decimal("60.0000")
    assert Decimal(str(bal_b["balance"])) == Decimal("40.0000")