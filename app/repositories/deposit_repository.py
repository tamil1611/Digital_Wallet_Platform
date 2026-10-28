
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.deposit import Deposit


class DepositRepository:

    @staticmethod
    def create(
        db: Session,
        deposit: Deposit,
    ) -> Deposit:
        db.add(deposit)
        db.flush()
        return deposit

    @staticmethod
    def get_by_id(
        db: Session,
        deposit_id: int,
    ) -> Deposit | None:
        statement = select(Deposit).where(
            Deposit.id == deposit_id
        )
        return db.scalar(statement)

    @staticmethod
    def get_by_reference_number(
        db: Session,
        reference_number: str,
    ) -> Deposit | None:
        statement = select(Deposit).where(
            Deposit.reference_number == reference_number
        )
        return db.scalar(statement)

    @staticmethod
    def get_by_wallet_id(
        db: Session,
        wallet_id: int,
    ) -> list[Deposit]:
        statement = (
            select(Deposit)
            .where(Deposit.wallet_id == wallet_id)
            .order_by(Deposit.created_at.desc())
        )
        return list(db.scalars(statement).all())

