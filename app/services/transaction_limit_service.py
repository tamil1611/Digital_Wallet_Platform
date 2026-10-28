
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.transaction_limit_repository import (
    TransactionLimitRepository,
)
from app.schemas.transaction_limit import (
    TransactionLimitResponse,
    TransactionLimitUpdate,
)


class TransactionLimitService:

    @staticmethod
    def get_limits(db: Session) -> TransactionLimitResponse:
        limits = TransactionLimitRepository.get_limits(db)

        if limits is None:
            limits = TransactionLimitRepository.create_default_limits(db)

            try:
                db.commit()
                db.refresh(limits)
            except Exception:
                db.rollback()
                raise

        return TransactionLimitResponse.model_validate(limits)

    @staticmethod
    def update_limits(
        db: Session,
        payload: TransactionLimitUpdate,
    ) -> TransactionLimitResponse:
        updates = payload.model_dump(exclude_unset=True)

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one transaction limit must be provided",
            )

        limits = TransactionLimitRepository.get_limits(db)

        if limits is None:
            limits = TransactionLimitRepository.create_default_limits(db)
            db.flush()

        for field, value in updates.items():
            setattr(limits, field, value)

        try:
            db.commit()
            db.refresh(limits)
        except Exception:
            db.rollback()
            raise

        return TransactionLimitResponse.model_validate(limits)

