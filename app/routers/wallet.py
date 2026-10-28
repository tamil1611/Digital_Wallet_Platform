
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.wallet_permissions import get_authorized_wallet
from app.database import get_db
from app.models.user import User
from app.models.wallet import Wallet
from app.repositories.wallet_repository import WalletRepository
from app.schemas.wallet import WalletCreate, WalletResponse, WalletUpdate
from app.services.wallet_service import WalletService
from app.services.audit_log_service import AuditLogService


router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.post(
    "/",
    response_model=WalletResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_wallet(
    wallet_data: WalletCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        wallet = WalletService.create_wallet(
            db=db,
            current_user=current_user,
            currency=wallet_data.currency,
        )

        AuditLogService.create_log(
            db=db,
            user_id=current_user.id,
            action="WALLET_CREATED",
            entity="WALLET",
            entity_id=wallet.id,
            request=request,
            metadata={
                "currency": wallet.currency,
                "status": wallet.status,
            },
        )

        db.commit()
        return wallet

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("/", response_model=list[WalletResponse])
def get_my_wallets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return WalletService.get_user_wallets(
        db=db,
        current_user=current_user,
    )


@router.get("/me", response_model=WalletResponse)
def get_my_wallet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = WalletRepository.get_by_user_id(
        db=db,
        user_id=current_user.id,
    )

    if wallet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found",
        )

    if wallet.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Wallet is not active",
        )

    return wallet


@router.get("/{wallet_id}", response_model=WalletResponse)
def get_wallet_by_id(
    wallet: Wallet = Depends(get_authorized_wallet),
):
    return wallet


@router.patch(
    "/{wallet_id}",
    response_model=WalletResponse,
)
def update_wallet(
    wallet_id: int,
    wallet_data: WalletUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return WalletService.update_wallet(
            db=db,
            wallet_id=wallet_id,
            current_user=current_user,
            wallet_data=wallet_data,
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


@router.post(
    "/{wallet_id}/freeze",
    response_model=WalletResponse,
)
def freeze_wallet(
    wallet_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        wallet = WalletService.freeze_wallet(
            db=db,
            wallet_id=wallet_id,
            current_user=current_user,
        )

        AuditLogService.create_log(
            db=db,
            user_id=current_user.id,
            action="WALLET_FROZEN",
            entity="WALLET",
            entity_id=wallet.id,
            request=request,
            metadata={"status": wallet.status},
        )

        db.commit()
        return wallet

    except ValueError as exc:
        message = str(exc)
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
                if message == "Wallet not found"
                else status.HTTP_400_BAD_REQUEST
            ),
            detail=message,
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.post(
    "/{wallet_id}/unfreeze",
    response_model=WalletResponse,
)
def unfreeze_wallet(
    wallet_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        wallet = WalletService.unfreeze_wallet(
            db=db,
            wallet_id=wallet_id,
            current_user=current_user,
        )

        AuditLogService.create_log(
            db=db,
            user_id=current_user.id,
            action="WALLET_UNFROZEN",
            entity="WALLET",
            entity_id=wallet.id,
            request=request,
            metadata={"status": wallet.status},
        )

        db.commit()
        return wallet

    except ValueError as exc:
        message = str(exc)
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
                if message == "Wallet not found"
                else status.HTTP_400_BAD_REQUEST
            ),
            detail=message,
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
