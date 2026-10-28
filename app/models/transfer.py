from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransferStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"



class Transfer(Base):
    __tablename__ = "transfers"

    __table_args__ = (
        Index("ix_transfers_sender_wallet_id", "sender_wallet_id"),
        Index("ix_transfers_receiver_wallet_id", "receiver_wallet_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    sender_wallet_id: Mapped[int] = mapped_column(
        ForeignKey("wallets.id", ondelete="RESTRICT"),
        nullable=False,
    )

    receiver_wallet_id: Mapped[int] = mapped_column(
        ForeignKey("wallets.id", ondelete="RESTRICT"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    status: Mapped[TransferStatus] = mapped_column(
        SQLAlchemyEnum(
            TransferStatus,
            name="transfer_status",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        default=TransferStatus.PENDING,
        nullable=False,
    )

    reference: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        default=lambda: f"TRF-{uuid4().hex.upper()}",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    retry_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        server_default="0",
    )

    last_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

