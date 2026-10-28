
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session


from app.core.dependencies import get_current_user, get_db
from app.models.transfer import Transfer
from app.models.user import User
from app.schemas.transfer import TransferCreate, TransferResponse
from app.services.transfer_service import TransferService
from fastapi import Request
from app.services.audit_log_service import AuditLogService

router = APIRouter(
    prefix="/api/transfers",
    tags=["Money Transfers"],
)


@router.post(
    "",
    response_model=TransferResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transfer(
    transfer_data: TransferCreate,
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=1, max_length=255),
    ],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TransferService.create_transfer(
        db=db,
        transfer_data=transfer_data,
        current_user_id=current_user.id,
        idempotency_key=idempotency_key,
    )


@router.get(
    "",
    response_model=list[TransferResponse],
)
def get_transfers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TransferService.get_transfers(
        db=db,
        current_user_id=current_user.id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{transfer_id}",
    response_model=TransferResponse,
)
def get_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TransferService.get_transfer(
        db=db,
        transfer_id=transfer_id,
        current_user_id=current_user.id,
    )


@router.post(
    "/{transfer_id}/cancel",
    response_model=TransferResponse,
)
def cancel_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TransferService.cancel_transfer(
        db=db,
        transfer_id=transfer_id,
        current_user_id=current_user.id,
    )