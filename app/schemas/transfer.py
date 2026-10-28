from decimal import Decimal
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.transaction import TransactionResponse


class TransferCreate(BaseModel):
    source_account_id: UUID
    destination_account_id: UUID
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = Field(default="", max_length=500)
    reference_id: str = Field(..., min_length=1, max_length=255)


class TransferResponse(BaseModel):
    message: str
    transfer_reference: str
    source_transaction: TransactionResponse
    destination_transaction: TransactionResponse