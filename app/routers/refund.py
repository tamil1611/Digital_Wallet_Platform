from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.refund import RefundCreate, RefundReject, RefundResponse
from app.services.refund_service import RefundService

router = APIRouter(
prefix="/api/refunds",
tags=["Refunds"],
)

@router.post("",
   response_model=RefundResponse,
   status_code=status.HTTP_201_CREATED,
)
def create_refund(
   refund_data: RefundCreate,
   db: Annotated[Session, Depends(get_db)],
   current_user: Annotated[User, Depends(get_current_user)],
    ):
   return RefundService.create_refund(
   db=db,
   original_transaction_id=refund_data.original_transaction_id,
   amount=refund_data.amount,
   reason=refund_data.reason,
   current_user=current_user,
)

@router.get("",
    response_model=list[RefundResponse],
)
def get_refunds(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return RefundService.get_refunds(
    db=db,
    current_user=current_user,
)

@router.get(
"/{refund_id}",
response_model=RefundResponse,
)
def get_refund(
   refund_id: int,
   db: Annotated[Session, Depends(get_db)],
   current_user: Annotated[User, Depends(get_current_user)],
):
   return RefundService.get_refund(
   db=db,
   refund_id=refund_id,
  current_user=current_user,
)

@router.post("/{refund_id}/approve",
   response_model=RefundResponse,
)
def approve_refund(
  refund_id: int,
  db: Annotated[Session, Depends(get_db)],
  current_user: Annotated[User, Depends(get_current_user)],
):
  return RefundService.approve_refund(
  db=db,
  refund_id=refund_id,
  current_user=current_user,
)

@router.post("/{refund_id}/reject",
   response_model=RefundResponse,
)
def reject_refund(
   refund_id: int,
   refund_data: RefundReject,
   db: Annotated[Session, Depends(get_db)],
   current_user: Annotated[User, Depends(get_current_user)],
):
   return RefundService.reject_refund(
   db=db,
   refund_id=refund_id,
   current_user=current_user,
   rejection_reason=refund_data.rejection_reason,
)
