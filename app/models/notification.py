
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NotificationType(str, Enum):
    DEPOSIT_COMPLETED = "DEPOSIT_COMPLETED"
    DEPOSIT_FAILED = "DEPOSIT_FAILED"

    TRANSFER_RECEIVED = "TRANSFER_RECEIVED"
    TRANSFER_COMPLETED = "TRANSFER_COMPLETED"
    TRANSFER_FAILED = "TRANSFER_FAILED"

    WITHDRAWAL_COMPLETED = "WITHDRAWAL_COMPLETED"
    WITHDRAWAL_FAILED = "WITHDRAWAL_FAILED"

    WALLET_FROZEN = "WALLET_FROZEN"
    WALLET_UNFROZEN = "WALLET_UNFROZEN"

    REFUND_APPROVED = "REFUND_APPROVED"

    SUSPICIOUS_TRANSACTION_DETECTED = (
        "SUSPICIOUS_TRANSACTION_DETECTED"
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    notification_type: Mapped[NotificationType] = mapped_column(
        SQLAlchemyEnum(
            NotificationType,
            name="notification_type",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

