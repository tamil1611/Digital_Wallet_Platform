
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transaction_limit import TransactionLimit


class TransactionLimitRepository:

    @staticmethod
    def get_limits(db: Session) -> TransactionLimit | None:
        statement = (
            select(TransactionLimit)
            .order_by(TransactionLimit.id)
            .limit(1)
        )

        return db.scalar(statement)

    @staticmethod
    def create_default_limits(
        db: Session,
    ) -> TransactionLimit:
        limits = TransactionLimit(
            max_transaction_amount=50000,
            daily_transfer_limit=100000,
            daily_withdrawal_limit=10000,
            max_transactions_per_day=20,
        )

        db.add(limits)
        db.flush()

        return limits

