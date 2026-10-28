import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    # Numeric(18, 4) avoids floating-point rounding errors
    balance = Column(Numeric(18, 4), nullable=False, default=0.0000)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    transactions = relationship(
        "Transaction", back_populates="account", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # DB-level guarantee: account balance can never drop below zero
        CheckConstraint("balance >= 0", name="chk_account_balance_non_negative"),
    )