from decimal import Decimal
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict


class TransactionCreate(BaseModel):
    type: Literal["credit", "debit"]
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = Field(default="", max_length=500)
    reference_id: str = Field(..., min_length=1, max_length=255)


class TransactionResponse(BaseModel):
    id: UUID
    account_id: UUID
    type: str
    amount: Decimal
    description: str
    reference_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedTransactionResponse(BaseModel):
    current_page: int
    page_size: int
    total_records: int
    total_pages: int
    data: List[TransactionResponse]