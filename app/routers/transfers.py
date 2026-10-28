from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.transfer import TransferCreate, TransferResponse
from app.services.transfer_service import TransferService

router = APIRouter(prefix="/api/v1/transfers", tags=["Transfers (Bonus)"])


@router.post("", response_model=TransferResponse, status_code=status.HTTP_200_OK)
def transfer_money(payload: TransferCreate, db: Session = Depends(get_db)):
    debit_tx, credit_tx = TransferService.transfer_funds(
        db=db,
        source_id=payload.source_account_id,
        dest_id=payload.destination_account_id,
        amount=payload.amount,
        description=payload.description or "",
        reference_id=payload.reference_id,
    )
    return {
        "message": "Transfer processed successfully",
        "transfer_reference": payload.reference_id,
        "source_transaction": debit_tx,
        "destination_transaction": credit_tx,
    }