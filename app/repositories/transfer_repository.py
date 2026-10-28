
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.transfer import Transfer


class TransferRepository:

    @staticmethod
    def create(db: Session, transfer: Transfer) -> Transfer:
        db.add(transfer)
        db.flush()
        return transfer

    @staticmethod
    def get_by_id(db: Session, transfer_id: int) -> Transfer | None:
        statement = select(Transfer).where(Transfer.id == transfer_id)
        return db.scalar(statement)

    @staticmethod
    def get_by_reference(db: Session, reference: str) -> Transfer | None:
        statement = select(Transfer).where(
            Transfer.reference == reference
        )
        return db.scalar(statement)

    @staticmethod
    def get_user_transfers(
        db: Session,
        wallet_ids: list[int],
        skip: int = 0,
        limit: int = 20,
    ) -> list[Transfer]:
        if not wallet_ids:
            return []

        statement = (
            select(Transfer)
            .where(
                or_(
                    Transfer.sender_wallet_id.in_(wallet_ids),
                    Transfer.receiver_wallet_id.in_(wallet_ids),
                )
            )
            .order_by(Transfer.created_at.desc(), Transfer.id.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(db.scalars(statement).all())

