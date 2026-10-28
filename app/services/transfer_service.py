from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.transaction import Transaction
from app.exceptions import LedgerException


class TransferService:
    
    @staticmethod
    def transfer_funds(
        db: Session,
        source_id: UUID,
        dest_id: UUID,
        amount: Decimal,
        description: str,
        reference_id: str,
    ):
        if source_id == dest_id:
            raise LedgerException(
                400, "INVALID_TRANSFER", "Source and destination accounts must be distinct."
            )

        # 1. Idempotency check across involved accounts
        existing_tx = (
            db.query(Transaction)
            .filter(
                Transaction.account_id.in_([source_id, dest_id]),
                Transaction.reference_id == reference_id.strip(),
            )
            .first()
        )
        if existing_tx:
            raise LedgerException(
                409, "DUPLICATE_TRANSACTION", "A transaction with this reference_id already exists."
            )

        # 2. Deadlock prevention: sort account IDs so locks are always acquired in consistent order
        sorted_ids = sorted([source_id, dest_id], key=lambda x: str(x))
        locked_accounts = (
            db.query(Account)
            .filter(Account.id.in_(sorted_ids))
            .order_by(Account.id)
            .with_for_update()
            .all()
        )

        if len(locked_accounts) != 2:
            raise LedgerException(
                404, "ACCOUNTS_NOT_FOUND", "One or both accounts were not found."
            )

        account_map = {acc.id: acc for acc in locked_accounts}
        source_account = account_map[source_id]
        dest_account = account_map[dest_id]

        # 3. Sufficient funds check
        if source_account.balance < amount:
            raise LedgerException(
                400,
                "INSUFFICIENT_FUNDS",
                f"Source account has insufficient balance ({source_account.balance:.2f}).",
            )

        # 4. Atomic balance updates
        source_account.balance -= amount
        dest_account.balance += amount

        # 5. Dual ledger records linking the transfer
        debit_entry = Transaction(
            account_id=source_id,
            type="debit",
            amount=amount,
            description=f"Transfer to {dest_id}: {description or ''}",
            reference_id=reference_id.strip(),
        )
        credit_entry = Transaction(
            account_id=dest_id,
            type="credit",
            amount=amount,
            description=f"Transfer from {source_id}: {description or ''}",
            reference_id=reference_id.strip(),
        )

        db.add_all([debit_entry, credit_entry])
        db.commit()
        db.refresh(debit_entry)
        db.refresh(credit_entry)

        return debit_entry, credit_entry