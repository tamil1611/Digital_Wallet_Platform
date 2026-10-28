
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.transaction_limit import TransactionLimit
from app.models.wallet import Wallet


class TransactionCountService:

    @staticmethod
    def validate_daily_transaction_count(
        db: Session,
        user_id: int,
        current_transaction_type: str,
    ) -> None:
        """
        Validate the maximum number of completed financial
        operations allowed per user per UTC day.

        TRANSFER_CREDIT is excluded because a transfer creates
        both debit and credit ledger entries. Counting only
        TRANSFER_DEBIT prevents counting one transfer twice.
        """

        limits = db.scalar(
            select(TransactionLimit)
            .order_by(TransactionLimit.id)
            .limit(1)
        )

        if limits is None:
            raise ValueError(
                "Transaction limits are not configured"
            )

        now = datetime.now(timezone.utc)

        day_start = datetime.combine(
            now.date(),
            time.min,
            tzinfo=timezone.utc,
        )
        day_end = day_start + timedelta(days=1)

        countable_types = [
            "DEPOSIT",
            "WITHDRAWAL",
            "TRANSFER_DEBIT",
            "REFUND",
        ]

        statement = (
            select(func.count(Transaction.id))
            .join(
                Wallet,
                Transaction.wallet_id == Wallet.id,
            )
            .where(
                Wallet.user_id == user_id,
                Transaction.status == "COMPLETED",
                Transaction.transaction_type.in_(countable_types),
                Transaction.created_at >= day_start,
                Transaction.created_at < day_end,
            )
        )

        completed_count = db.scalar(statement) or 0

        if completed_count >= limits.max_transactions_per_day:
            raise ValueError(
                "Daily transaction limit of "
                f"{limits.max_transactions_per_day} transactions exceeded"
            )

