import math
from uuid import UUID
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.transaction import Transaction
from app.exceptions import LedgerException
from app.services.account_service import AccountService


class LedgerService:
    
    @staticmethod
    def add_transaction(
        db: Session,
        account_id: UUID,
        tx_type: str,
        amount: Decimal,
        description: str,
        reference_id: str,
    ) -> Transaction:
        # 1. Idempotency check: don't alter balance if reference already exists
        existing_tx = (
            db.query(Transaction)
            .filter(
                Transaction.account_id == account_id,
                Transaction.reference_id == reference_id.strip(),
            )
            .first()
        )
        if existing_tx:
            raise LedgerException(
                409,
                "DUPLICATE_TRANSACTION",
                f"Transaction with reference_id '{reference_id}' already exists.",
            )

        # 2. Acquire pessimistic lock on the account row to prevent race conditions
        account = (
            db.query(Account)
            .filter(Account.id == account_id)
            .with_for_update()
            .first()
        )
        if not account:
            raise LedgerException(
                404, "ACCOUNT_NOT_FOUND", f"Account '{account_id}' does not exist."
            )

        # 3. Balance verification for debits
        if tx_type == "debit" and account.balance < amount:
            raise LedgerException(
                400,
                "INSUFFICIENT_FUNDS",
                f"Insufficient funds. Balance: {account.balance:.2f}, Requested: {amount:.2f}.",
            )

        # 4. Update balance
        if tx_type == "credit":
            account.balance += amount
        else:
            account.balance -= amount

        # 5. Append ledger entry
        new_tx = Transaction(
            account_id=account_id,
            type=tx_type,
            amount=amount,
            description=description or "",
            reference_id=reference_id.strip(),
        )
        db.add(new_tx)

        # Commits both balance update and ledger entry atomically
        db.commit()
        db.refresh(new_tx)
        return new_tx

    @staticmethod
    def get_transaction_history(
        db: Session,
        account_id: UUID,
        tx_type: Optional[str],
        page: int,
        limit: int,
    ):
        # Validate account exists
        AccountService.get_account_or_404(db, account_id)

        query = db.query(Transaction).filter(Transaction.account_id == account_id)
        if tx_type:
            query = query.filter(Transaction.type == tx_type)

        total_records = query.count()
        total_pages = math.ceil(total_records / limit) if total_records > 0 else 1
        offset = (page - 1) * limit

        transactions = (
            query.order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "current_page": page,
            "page_size": limit,
            "total_records": total_records,
            "total_pages": total_pages,
            "data": transactions,
        }