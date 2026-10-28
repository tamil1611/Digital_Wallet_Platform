from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refund import Refund

class RefundRepository:


    @staticmethod
    def create(db: Session, refund: Refund) -> Refund:
      db.add(refund)
      db.flush()
      return refund

    @staticmethod
    def get_by_id(db: Session, refund_id: int) -> Refund | None:
      statement = select(Refund).where(Refund.id == refund_id)
      return db.scalar(statement)

    @staticmethod
    def get_by_id_for_update(
       db: Session,
       refund_id: int,
) -> Refund | None:
        statement = (
        select(Refund)
        .where(Refund.id == refund_id)
        .with_for_update()
    )
        return db.scalar(statement)

    @staticmethod
    def get_by_original_transaction(
       db: Session,
       transaction_id: int,
) -> Refund | None:
       statement = select(Refund).where(
        Refund.original_transaction_id == transaction_id
    )
       return db.scalar(statement)

    @staticmethod
    def list_all(db: Session) -> list[Refund]:
       statement = select(Refund).order_by(Refund.created_at.desc())
       return list(db.scalars(statement).all())

    @staticmethod
    def list_by_wallet(
       db: Session,
       wallet_id: int,
     ) -> list[Refund]:
       statement = (
        select(Refund)
        .where(Refund.wallet_id == wallet_id)
        .order_by(Refund.created_at.desc())
    )
       return list(db.scalars(statement).all())

