from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    wallet_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wallets.id"),
        nullable=False,
        index=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    balance_before: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
    )

    reference_entity: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    reference_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    transaction_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="check_transaction_amount_positive",
        ),
        CheckConstraint(
            "balance_before >= 0 AND balance_after >= 0",
            name="check_transaction_balances_nonnegative",
        ),
        CheckConstraint(
            """
            transaction_type IN (
                'DEPOSIT',
                'WITHDRAWAL',
                'TRANSFER_DEBIT',
                'TRANSFER_CREDIT',
                'REFUND',
                'FEE',
                'ADJUSTMENT',
                'REVERSAL'
            )
            """,
            name="check_transaction_type",
        ),
        CheckConstraint(
            """
             status IN (
               'PENDING',
               'PROCESSING',
               'REVIEW_REQUIRED',
               'COMPLETED',
               'FAILED',
               'CANCELLED'
             )
              """,
            name="check_transaction_status",
            ),
    )