from decimal import Decimal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    # Forbid extra fields so clients cannot inject initial balance
    model_config = ConfigDict(extra="forbid")


class AccountResponse(BaseModel):
    id: UUID
    name: str
    balance: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountBalanceResponse(BaseModel):
    account_id: UUID
    balance: Decimal