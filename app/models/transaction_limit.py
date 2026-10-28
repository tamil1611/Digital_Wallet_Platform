
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransactionLimit(Base):
    __tablename__ = "transaction_limits"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    max_transaction_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("50000.00"),
        
        
    )
    
    suspicious_amount_threshold: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("10000.00"),
        server_default="10000.00",
    )

    daily_transfer_limit: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("100000.00"),
    )

    daily_withdrawal_limit: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("10000.00"),
    )

    max_transactions_per_day: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=20,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

