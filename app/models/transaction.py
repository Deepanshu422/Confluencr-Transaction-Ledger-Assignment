import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    type = Column(String(10), nullable=False)
    amount = Column(Numeric(18, 4), nullable=False)
    description = Column(String(500), nullable=False, default="")
    reference_id = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    account = relationship("Account", back_populates="transactions")

    __table_args__ = (
        CheckConstraint("type IN ('credit', 'debit')", name="chk_tx_type"),
        CheckConstraint("amount > 0", name="chk_tx_amount_positive"),
        # Idempotency: same reference_id cannot be reused for the same account
        UniqueConstraint("account_id", "reference_id", name="uq_account_reference"),
        Index("idx_transactions_account_created", "account_id", created_at.desc()),
    )