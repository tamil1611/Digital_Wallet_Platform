
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.permissions import require_roles
from app.models.user import User
from app.schemas.transaction_limit import (
    TransactionLimitResponse,
    TransactionLimitUpdate,
)
from app.services.transaction_limit_service import (
    TransactionLimitService,
)

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
)


@router.get(
    "/transaction-limits",
    response_model=TransactionLimitResponse,
)
def get_transaction_limits(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("SUPER_ADMIN", "ADMIN")
    ),
):
    return TransactionLimitService.get_limits(db)


@router.patch(
    "/transaction-limits",
    response_model=TransactionLimitResponse,
)
def update_transaction_limits(
    payload: TransactionLimitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("SUPER_ADMIN", "ADMIN")
    ),
):
    return TransactionLimitService.update_limits(db, payload)
