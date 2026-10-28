# Transaction Ledger API

A robust, production-grade backend API for a transaction ledger system. Built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**.

## 🏗️ Architectural Decisions & Integrity Guarantees

This service was designed with strict financial engineering principles in mind:

1. **Pessimistic Row-Level Locking (`SELECT ... FOR UPDATE`)**: Balances are updated safely. If concurrent debit requests hit the same account simultaneously, the database locks the row, forcing sequential execution to completely eliminate double-spending race conditions.
2. **Deadlock Prevention**: In the bonus transfer endpoint, account locks are always acquired in deterministic (alphabetical UUID) order, guaranteeing cyclic deadlocks cannot occur.
3. **Database-Level Invariants**: 
   - `CHECK (balance >= 0)` ensures an account can never go negative even if application logic fails.
   - `NUMERIC(18, 4)` is used for all monetary values to completely eliminate floating-point rounding errors.
4. **Idempotency**: Implemented a composite unique index (`UNIQUE(account_id, reference_id)`) at the database level. Duplicate network requests return a `409 Conflict` gracefully without altering the ledger.
5. **Strict Input Validation**: Pydantic `extra="forbid"` is utilized on the account creation schema, physically preventing clients from attempting to inject an initial balance.

## 🚀 Quick Start (Developer Experience)

This project includes a `Makefile` to automate the local development and testing workflow. 

### Prerequisites
- Python 3.11+
- Docker & Docker Compose

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/Deepanshu422/Confluencr-Transaction-Ledger-Assignment.git
cd Confluencr-Transaction-Ledger-Assignment

# Configure environment
cp .env.example .env

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
make install

```

### 2. The Development Loop

Instead of memorizing long commands, use the provided `Makefile`:

* **`make db-up`** — Starts the PostgreSQL database in the background via Docker.
* **`make run`** — Starts the FastAPI server locally (`http://localhost:8000`).
* **`make test`** — Runs the full `pytest` suite covering concurrency and validation edge cases.
* **`make db-down`** — Stops the database and wipes the volume for a fresh start.
* **`make clean`** — Removes cached Python and pytest files.

*(Run just `make` to see the full help menu in your terminal).*

## 🧪 Automated Testing

```bash
make test

```

The test suite validates:

* Enforcement of `0.00` initial balances.
* Proper credit increments and debit decrements.
* Hard rejections on insufficient funds.
* Rejection of duplicate `reference_id` payload replays.
* Multi-account atomic transfers.
* **Concurrency Safety:** A stress test demonstrating that two simultaneous debits of ₹100 on a ₹100 balance safely process one and reject the other.

## 📚 API Documentation

FastAPI automatically generates interactive documentation. Once the server is running (`make run`), visit:

* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)

### cURL Examples

**1. Create an Account**

```bash
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Deepanshu Singh"}'

```

**2. Add a Transaction (Credit/Debit)**

```bash
curl -X POST http://localhost:8000/api/v1/accounts/<ACCOUNT_ID>/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "type": "credit",
    "amount": 1000.50,
    "description": "Initial Deposit",
    "reference_id": "txn-001"
  }'

```

**3. Get Balance**

```bash
curl http://localhost:8000/api/v1/accounts/<ACCOUNT_ID>/balance

```

**4. Get Transaction History (Paginated)**

```bash
curl "http://localhost:8000/api/v1/accounts/<ACCOUNT_ID>/transactions?page=1&limit=10&type=credit"

```

**5. Transfer Funds (Bonus)**

```bash
curl -X POST http://localhost:8000/api/v1/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "source_account_id": "<ACCOUNT_A_ID>",
    "destination_account_id": "<ACCOUNT_B_ID>",
    "amount": 250.00,
    "description": "Invoice Payment",
    "reference_id": "transfer-abc-123"
  }'

```

```

```