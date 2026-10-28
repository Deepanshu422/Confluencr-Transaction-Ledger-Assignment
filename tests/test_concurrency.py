import concurrent.futures
from decimal import Decimal

def test_concurrent_debits_prevent_double_spend(client):
    # 1. Create Account
    acc_res = client.post("/api/v1/accounts", json={"name": "Race Condition Tester"})
    assert acc_res.status_code == 201
    account_id = acc_res.json()["id"]

    # 2. Credit 100
    client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={"type": "credit", "amount": 100.0, "reference_id": "init-100"}
    )

    # 3. Fire 2 simultaneous debit attempts of 100
    def perform_debit(ref_id):
        return client.post(
            f"/api/v1/accounts/{account_id}/transactions",
            json={"type": "debit", "amount": 100.0, "reference_id": ref_id}
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(perform_debit, "tx-debit-A")
        f2 = executor.submit(perform_debit, "tx-debit-B")
        res1 = f1.result()
        res2 = f2.result()

    statuses = sorted([res1.status_code, res2.status_code])
    
    # One request MUST acquire the lock, see 100, and succeed (201).
    # The second MUST wait for the lock, see 0, and fail (400).
    assert statuses == [201, 400]

    # 4. Verify final balance is exactly 0.00, not negative
    bal_res = client.get(f"/api/v1/accounts/{account_id}/balance")
    assert Decimal(str(bal_res.json()["balance"])) == Decimal("0.0000")