from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.transaction_limit import TransactionLimit
from app.models.suspicious_transaction import (
    SuspiciousStatus,
    SuspiciousTransactionAlert,
)
from app.models.wallet import Wallet
from app.models.transfer import Transfer, TransferStatus
from app.models.notification import NotificationType
from app.services.notification_service import NotificationService
from app.models.audit_log import AuditLog

class SuspiciousTransactionService:
    """
    Rule-based suspicious transaction detection.

    Initial configurable-by-code thresholds:
    - High amount: TransactionLimit.max_transaction_amount
    - Multiple transfers: 3 or more in 5 minutes
    - Unusual frequency: 5 or more financial transactions in 10 minutes
    """

    TRANSFER_WINDOW_MINUTES = 5
    TRANSFER_COUNT_THRESHOLD = 3

    FREQUENCY_WINDOW_MINUTES = 10
    FREQUENCY_THRESHOLD = 5

    @staticmethod
    def evaluate_transaction(
        db: Session,
        wallet_id: int,
        amount: Decimal,
        transaction_type: str,
    ) -> dict:
        """
        Evaluate transaction risk before creating the final ledger entry.

        This method does not create or update ledger records.
        The caller owns the database transaction.
        """

        now = datetime.now(timezone.utc)

        wallet = db.get(Wallet, wallet_id)

        if wallet is None:
            return {
                "status": SuspiciousStatus.NORMAL.value,
                "reasons": [],
            }

        reasons: list[str] = []

        limits = db.scalar(
            select(TransactionLimit)
            .order_by(TransactionLimit.id)
            .limit(1)
        )

        # Rule 1: High-value transaction.
        if (
            limits is not None
            and amount > limits.max_transaction_amount
        ):
            reasons.append(
                "TRANSACTION_AMOUNT_EXCEEDS_CONFIGURED_THRESHOLD"
            )

        # Rule 2: Multiple recent transfers.
        transfer_window_start = now - timedelta(
            minutes=SuspiciousTransactionService.TRANSFER_WINDOW_MINUTES
        )

        recent_transfer_count = db.scalar(
            select(func.count(Transfer.id)).where(
                Transfer.sender_wallet_id == wallet.id,
                Transfer.status == TransferStatus.COMPLETED,
                Transfer.completed_at >= transfer_window_start,
                Transfer.completed_at <= now,
            )
        ) or 0

        if (
            transaction_type == "TRANSFER_DEBIT"
            and recent_transfer_count
            >= SuspiciousTransactionService.TRANSFER_COUNT_THRESHOLD
        ):
            reasons.append(
                "MULTIPLE_TRANSFERS_WITHIN_SHORT_PERIOD"
            )

        # Rule 3: Unusual transaction frequency.
        frequency_window_start = now - timedelta(
            minutes=SuspiciousTransactionService.FREQUENCY_WINDOW_MINUTES
        )

        recent_transaction_count = db.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.wallet_id == wallet.id,
                Transaction.status.in_(["COMPLETED", "PROCESSING"]),
                Transaction.created_at >= frequency_window_start,
                Transaction.created_at <= now,
            )
        ) or 0

        if (
            recent_transaction_count + 1
            >= SuspiciousTransactionService.FREQUENCY_THRESHOLD
        ):
            reasons.append("UNUSUAL_TRANSACTION_FREQUENCY")

        # Rule 4: Wallet is frozen.
        if wallet.status.value == "FROZEN":
            reasons.append("WALLET_FROZEN")

        # Rule 5: Daily transaction count limit.
        if limits is not None:
            day_start = now.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            countable_types = [
                "DEPOSIT",
                "WITHDRAWAL",
                "TRANSFER_DEBIT",
                "REFUND",
            ]

            daily_count = db.scalar(
                select(func.count(Transaction.id))
                .join(Wallet, Transaction.wallet_id == Wallet.id)
                .where(
                    Wallet.user_id == wallet.user_id,
                    Transaction.status == "COMPLETED",
                    Transaction.transaction_type.in_(countable_types),
                    Transaction.created_at >= day_start,
                    Transaction.created_at <= now,
                )
            ) or 0

            if daily_count + 1 > limits.max_transactions_per_day:
                reasons.append(
                    "DAILY_TRANSACTION_COUNT_LIMIT_EXCEEDED"
                )

        # Decide risk status.
        blocking_reasons = {
            "WALLET_FROZEN",
            "DAILY_TRANSACTION_COUNT_LIMIT_EXCEEDED",
        }

        if any(reason in blocking_reasons for reason in reasons):
            risk_status = SuspiciousStatus.BLOCKED.value
        elif reasons:
            risk_status = SuspiciousStatus.REVIEW_REQUIRED.value
        else:
            risk_status = SuspiciousStatus.NORMAL.value

        return {
            "status": risk_status,
            "reasons": reasons,
        }
    @staticmethod
    def create_suspicious_notification(
        db: Session,
        wallet_id: int,
        reasons: list[str],
    ) -> None:
        wallet = db.get(Wallet, wallet_id)

        if wallet is None or not reasons:
            return

        NotificationService.create_notification(
            db=db,
            user_id=wallet.user_id,
            notification_type=(
                NotificationType.SUSPICIOUS_TRANSACTION_DETECTED
            ),
            title="Suspicious Transaction Detected",
            message=(
                f"A suspicious transaction was detected "
                f"on wallet ID {wallet.id}. "
                f"Reasons: {', '.join(reasons)}"
            ),
        )