from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.account import Account
from app.exceptions import LedgerException


class AccountService:
    
    @staticmethod
    def create_account(db: Session, name: str) -> Account:
        clean_name = name.strip()
        if not clean_name:
            raise LedgerException(400, "INVALID_NAME", "Account name cannot be empty.")

        account = Account(name=clean_name, balance=Decimal("0.0000"))
        db.add(account)
        db.commit()
        db.refresh(account)
        return account

    @staticmethod
    def get_account_or_404(db: Session, account_id: UUID) -> Account:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise LedgerException(
                404, "ACCOUNT_NOT_FOUND", f"Account '{account_id}' does not exist."
            )
        return account