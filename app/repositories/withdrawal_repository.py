
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.withdrawal import Withdrawal


class WithdrawalRepository:

    @staticmethod
    def create(
        db: Session,
        withdrawal: Withdrawal,
    ) -> Withdrawal:
        db.add(withdrawal)
        db.flush()
        return withdrawal

    @staticmethod
    def get_by_id(
        db: Session,
        withdrawal_id: int,
    ) -> Withdrawal | None:
        statement = select(Withdrawal).where(
            Withdrawal.id == withdrawal_id
        )
        return db.scalar(statement)

    @staticmethod
    def get_by_id_for_update(
        db: Session,
        withdrawal_id: int,
    ) -> Withdrawal | None:
        statement = (
            select(Withdrawal)
            .where(Withdrawal.id == withdrawal_id)
            .with_for_update()
        )
        return db.scalar(statement)

    @staticmethod
    def get_all(
        db: Session,
    ) -> list[Withdrawal]:
        statement = select(Withdrawal).order_by(
            Withdrawal.created_at.desc()
        )
        return list(db.scalars(statement).all())

