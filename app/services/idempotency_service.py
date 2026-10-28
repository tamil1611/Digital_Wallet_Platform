import hashlib
import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.idempotency import IdempotencyRecord
from app.repositories.idempotency_repository import IdempotencyRepository


class IdempotencyService:

    @staticmethod
    def generate_request_hash(request_data: dict[str, Any]) -> str:
        serialized_data = json.dumps(
            request_data,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

        return hashlib.sha256(
            serialized_data.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def get_existing_record(
        db: Session,
        user_id: int,
        idempotency_key: str,
        request_hash: str,
        operation: str,
    ) -> IdempotencyRecord | None:

        record = IdempotencyRepository.get_by_key(
            db=db,
            user_id=user_id,
            idempotency_key=idempotency_key,
        )

        if record is None:
            return None

        if record.operation != operation:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This Idempotency-Key was already used for another operation.",
            )

        if record.request_hash != request_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This Idempotency-Key was already used with a different request.",
            )

        if record.status == "COMPLETED":
            return record

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A request with this Idempotency-Key is already processing.",
        )

    @staticmethod
    def create_record(
        db: Session,
        user_id: int,
        idempotency_key: str,
        operation: str,
        request_hash: str,
    ) -> IdempotencyRecord:

        record = IdempotencyRecord(
            user_id=user_id,
            idempotency_key=idempotency_key,
            operation=operation,
            request_hash=request_hash,
            status="PROCESSING",
        )

        return IdempotencyRepository.create(
            db=db,
            record=record,
        )

    @staticmethod
    def complete_record(
        db: Session,
        record: IdempotencyRecord,
        response_body: dict[str, Any],
    ) -> IdempotencyRecord:

        record.status = "COMPLETED"
        record.response_body = response_body

        return IdempotencyRepository.save(
            db=db,
            record=record,
        )