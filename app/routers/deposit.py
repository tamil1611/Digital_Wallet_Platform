
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.deposit import DepositCreate, DepositResponse
from app.services.audit_log_service import AuditLogService
from app.services.deposit_service import DepositService

router = APIRouter(
    prefix="/deposits",
    tags=["Deposits"],
)


@router.post(
    "/wallets/{wallet_id}/deposits",
    response_model=DepositResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deposit(
    wallet_id: int,
    deposit_data: DepositCreate,
    request: Request,
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=1, max_length=255),
    ],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        deposit = DepositService.create_deposit(
            db=db,
            wallet_id=wallet_id,
            amount=deposit_data.amount,
            current_user=current_user,
            idempotency_key=idempotency_key,
        )

        AuditLogService.create_log(
            db=db,
            user_id=current_user.id,
            action="DEPOSIT_CREATED",
            entity="DEPOSIT",
            entity_id=deposit.id,
            request=request,
            metadata={
                "wallet_id": wallet_id,
                "amount": str(deposit_data.amount),
                "status": str(deposit.status),
            },
        )
        db.commit()
        return deposit

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get(
    "/",
    response_model=list[DepositResponse],
)
def get_deposits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DepositService.get_deposits(
        db=db,
        current_user=current_user,
    )


@router.get(
    "/{deposit_id}",
    response_model=DepositResponse,
)
def get_deposit_by_id(
    deposit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return DepositService.get_deposit(
            db=db,
            deposit_id=deposit_id,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
