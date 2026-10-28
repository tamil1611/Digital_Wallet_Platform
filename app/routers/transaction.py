
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.transaction_permissions import get_authorized_transaction
from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.transaction_service import TransactionService


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        transaction = TransactionService.create_transaction(
            db=db,
            current_user=current_user,
            wallet_id=transaction_data.wallet_id,
            transaction_type=transaction_data.transaction_type,
            amount=transaction_data.amount,
            description=transaction_data.description,
        )
        return transaction

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def get_transaction(
    transaction: Transaction = Depends(get_authorized_transaction),
):
    return transaction


@router.get(
    "/wallet/{wallet_id}",
    response_model=list[TransactionResponse],
)
def get_wallet_transactions(
    wallet_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        transactions = TransactionService.get_wallet_transactions(
            db=db,
            wallet_id=wallet_id,
            current_user=current_user,
            skip=skip,
            limit=limit,
        )
        return transactions

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/",
    tags=["Transactions"],
)
def get_transaction_history(
    wallet_id: int | None = Query(default=None, ge=1),
    transaction_type: str | None = Query(default=None, alias="type"),
    transaction_status: str | None = Query(default=None, alias="status"),
    min_amount: Decimal | None = Query(default=None, ge=0),
    max_amount: Decimal | None = Query(default=None, ge=0),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return TransactionService.get_transaction_history(
            db=db,
            current_user=current_user,
            wallet_id=wallet_id,
            transaction_type=transaction_type,
            transaction_status=transaction_status,
            min_amount=min_amount,
            max_amount=max_amount,
            from_date=from_date,
            to_date=to_date,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

