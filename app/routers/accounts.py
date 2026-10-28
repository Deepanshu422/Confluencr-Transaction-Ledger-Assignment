from uuid import UUID
from typing import Optional, Literal
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    AccountCreate,
    AccountResponse,
    AccountBalanceResponse,
    TransactionCreate,
    TransactionResponse,
    PaginatedTransactionResponse,
)
from app.services import AccountService, LedgerService

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    return AccountService.create_account(db, payload.name)


@router.get("/{account_id}/balance", response_model=AccountBalanceResponse)
def get_balance(account_id: UUID, db: Session = Depends(get_db)):
    account = AccountService.get_account_or_404(db, account_id)
    return {"account_id": account.id, "balance": account.balance}


@router.post(
    "/{account_id}/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_transaction(
    account_id: UUID, payload: TransactionCreate, db: Session = Depends(get_db)
):
    return LedgerService.add_transaction(
        db=db,
        account_id=account_id,
        tx_type=payload.type,
        amount=payload.amount,
        description=payload.description or "",
        reference_id=payload.reference_id,
    )


@router.get("/{account_id}/transactions", response_model=PaginatedTransactionResponse)
def get_transactions(
    account_id: UUID,
    type: Optional[Literal["credit", "debit"]] = Query(
        None, description="Filter by credit or debit"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    return LedgerService.get_transaction_history(
        db=db, account_id=account_id, tx_type=type, page=page, limit=limit
    )