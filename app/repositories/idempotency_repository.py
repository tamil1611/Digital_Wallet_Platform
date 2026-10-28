from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.idempotency import IdempotencyRecord


class IdempotencyRepository:

    @staticmethod
    def get_by_key(
        db: Session,
        user_id: int,
        idempotency_key: str,
    ) -> IdempotencyRecord | None:
        statement = select(IdempotencyRecord).where(
            IdempotencyRecord.user_id == user_id,
            IdempotencyRecord.idempotency_key == idempotency_key,
        )

        return db.scalar(statement)

    @staticmethod
    def create(
        db: Session,
        record: IdempotencyRecord,
    ) -> IdempotencyRecord:
        db.add(record)
        db.flush()
        return record

    @staticmethod
    def save(
        db: Session,
        record: IdempotencyRecord,
    ) -> IdempotencyRecord:
        db.add(record)
        db.flush()
        return record