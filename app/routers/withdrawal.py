from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.withdrawal import Withdrawal
from app.schemas.withdrawal import WithdrawalCreate, WithdrawalResponse
from app.services.withdrawal_service import WithdrawalService


router = APIRouter(
    tags=["Withdrawals"],
)


@router.post(
    "/api/wallets/{wallet_id}/withdrawals",
    response_model=WithdrawalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_withdrawal(
    wallet_id: int,
    withdrawal_data: WithdrawalCreate,
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=1, max_length=255),
    ],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return WithdrawalService.create_withdrawal(
            db=db,
            wallet_id=wallet_id,
            amount=withdrawal_data.amount,
            current_user=current_user,
            idempotency_key=idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get(
    "/api/withdrawals",
    response_model=list[WithdrawalResponse],
)
def get_withdrawals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return WithdrawalService.get_withdrawals(
            db=db,
            current_user=current_user,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get(
    "/api/withdrawals/{withdrawal_id}",
    response_model=WithdrawalResponse,
)
def get_withdrawal(
    withdrawal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return WithdrawalService.get_withdrawal(
            db=db,
            withdrawal_id=withdrawal_id,
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


@router.post(
    "/api/withdrawals/{withdrawal_id}/cancel",
    response_model=WithdrawalResponse,
)
def cancel_withdrawal(
    withdrawal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return WithdrawalService.cancel_withdrawal(
            db=db,
            withdrawal_id=withdrawal_id,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc