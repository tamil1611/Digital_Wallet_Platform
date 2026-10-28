from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refund import Refund, RefundStatus
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet, WalletStatus
from app.repositories.refund_repository import RefundRepository
from app.models.notification import NotificationType
from app.services.notification_service import NotificationService
from app.models.audit_log import AuditLog


class RefundService:

    @staticmethod
    def create_refund(
        db: Session,
        original_transaction_id: int,
        amount: Decimal,
        reason: str,
        current_user: User,
    ) -> Refund:
        try:
            if not amount.is_finite() or amount <= Decimal("0"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Refund amount must be greater than zero",
                )

            if amount != amount.quantize(Decimal("0.01")):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Refund amount can have at most 2 decimal places",
                )

            transaction_statement = (
                select(Transaction)
                .where(Transaction.id == original_transaction_id)
                .with_for_update()
            )
            original_transaction = db.scalar(transaction_statement)

            if original_transaction is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Original transaction not found",
                )

            if original_transaction.status != "COMPLETED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only completed transactions can be refunded",
                )

            # Refunds are allowed only for completed outgoing transactions.
            if original_transaction.transaction_type not in {
                "WITHDRAWAL",
                "TRANSFER_DEBIT",
                "FEE",
            }:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This transaction type cannot be refunded",
                )

            wallet_statement = (
                select(Wallet)
                .where(Wallet.id == original_transaction.wallet_id)
                .with_for_update()
            )
            wallet = db.scalar(wallet_statement)

            if wallet is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Wallet not found",
                )

            if (
                current_user.role == "CUSTOMER"
                and wallet.user_id != current_user.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to request this refund",
                )

            if wallet.status == WalletStatus.CLOSED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Refunds cannot be requested for a closed wallet",
                )

            existing_refund = RefundRepository.get_by_original_transaction(
                db=db,
                transaction_id=original_transaction_id,
            )

            if existing_refund is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A refund request already exists for this transaction",
                )

            if amount > original_transaction.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Refund amount cannot exceed the original transaction amount",
                )

            refund = Refund(
                original_transaction_id=original_transaction.id,
                wallet_id=wallet.id,
                requested_by=current_user.id,
                amount=amount,
                status=RefundStatus.REQUESTED.value,
                reason=reason.strip(),
            )

            RefundRepository.create(db=db, refund=refund)
            db.flush()

# Create refund audit log.
            audit_log = AuditLog(
              user_id=current_user.id,
              action="REFUND_CREATED",
              entity="REFUND",
              entity_id=str(refund.id),
              metadata_={
                 "wallet_id": refund.wallet_id,
                 "original_transaction_id": refund.original_transaction_id,
                 "amount": str(refund.amount),
                 "reason": refund.reason,
                 "status": refund.status,
                },
             )

            db.add(audit_log)
            db.commit()
            db.refresh(refund)

            return refund

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_refund(
        db: Session,
        refund_id: int,
        current_user: User,
    ) -> Refund:
        refund = RefundRepository.get_by_id(
            db=db,
            refund_id=refund_id,
        )

        if refund is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund not found",
            )

        wallet = db.get(Wallet, refund.wallet_id)

        if wallet is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found",
            )

        if (
            current_user.role == "CUSTOMER"
            and wallet.user_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this refund",
            )

        return refund

    @staticmethod
    def get_refunds(
        db: Session,
        current_user: User,
    ) -> list[Refund]:
        statement = (
            select(Refund)
            .join(Wallet, Refund.wallet_id == Wallet.id)
            .order_by(Refund.created_at.desc())
        )

        if current_user.role == "CUSTOMER":
            statement = statement.where(
                Wallet.user_id == current_user.id
            )

        return list(db.scalars(statement).all())

    @staticmethod
    def approve_refund(
        db: Session,
        refund_id: int,
        current_user: User,
    ) -> Refund:
        try:
            if current_user.role not in {
                "ADMIN",
                "SUPER_ADMIN",
                "SUPPORT_AGENT",
            }:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to approve refunds",
                )

            refund_statement = (
                select(Refund)
                .where(Refund.id == refund_id)
                .with_for_update()
            )
            refund = db.scalar(refund_statement)

            if refund is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Refund not found",
                )

            if refund.status not in {
                RefundStatus.REQUESTED.value,
                RefundStatus.UNDER_REVIEW.value,
            }:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Refund cannot be approved from status {refund.status}",
                )

            transaction_statement = (
                select(Transaction)
                .where(
                    Transaction.id == refund.original_transaction_id
                )
                .with_for_update()
            )
            original_transaction = db.scalar(transaction_statement)

            if (
                original_transaction is None
                or original_transaction.status != "COMPLETED"
                or original_transaction.transaction_type
                not in {"WITHDRAWAL", "TRANSFER_DEBIT", "FEE"}
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Original transaction is not eligible for a refund",
                )

            wallet_statement = (
                select(Wallet)
                .where(Wallet.id == refund.wallet_id)
                .with_for_update()
            )
            wallet = db.scalar(wallet_statement)

            if wallet is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Wallet not found",
                )

            if wallet.status == WalletStatus.CLOSED:
                refund.status = RefundStatus.FAILED
                refund.reviewed_by = current_user.id
                refund.reviewed_at = datetime.now(timezone.utc)

                db.commit()

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Refund cannot be completed for a closed wallet",
                )

            balance_before = Decimal(str(wallet.available_balance))
            balance_after = balance_before + refund.amount

            wallet.available_balance = balance_after

            now = datetime.now(timezone.utc)

            refund.status = RefundStatus.COMPLETED
            refund.reviewed_by = current_user.id
            refund.reviewed_at = now
            refund.completed_at = now

            ledger_entry = Transaction(
                wallet_id=wallet.id,
                transaction_type="REFUND",
                amount=refund.amount,
                balance_before=balance_before,
                balance_after=balance_after,
                status="COMPLETED",
                reference_entity="REFUND",
                reference_id=f"REF-{refund.id}-{uuid4().hex.upper()}",
                description=(
                    f"Refund for original transaction "
                    f"{refund.original_transaction_id}"
                ),
                created_by=current_user.id,
                transaction_metadata={
                    "refund_id": refund.id,
                    "original_transaction_id": (
                        refund.original_transaction_id
                    ),
                    "currency": wallet.currency,
                },
            )

            db.add(ledger_entry)
            
            # Create refund approval audit log.
            audit_log = AuditLog(
                user_id=current_user.id,
                action="REFUND_APPROVED",
                entity="REFUND",
                entity_id=str(refund.id),
                metadata_={
                   "wallet_id": wallet.id,
                   "original_transaction_id": refund.original_transaction_id,
                   "amount": str(refund.amount),
                   "currency": wallet.currency,
                   "status": refund.status,
                   "reviewed_by": current_user.id,
                },
            )

            db.add(audit_log)
            db.flush()
            
            NotificationService.create_notification(
               db=db,
               user_id=wallet.user_id,
               notification_type=NotificationType.REFUND_APPROVED,
               title="Refund Approved",
               message=(
                 f"Your refund of {refund.amount} {wallet.currency} "
                 f"has been approved successfully. "
                   f"Refund ID: {refund.id}"
                ),
            )
            db.commit()
            db.refresh(refund)

            return refund

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def reject_refund(
        db: Session,
        refund_id: int,
        current_user: User,
        rejection_reason: str,
    ) -> Refund:
        try:
            if current_user.role not in {
                "ADMIN",
                "SUPER_ADMIN",
                "SUPPORT_AGENT",
            }:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to reject refunds",
                )

            refund_statement = (
                select(Refund)
                .where(Refund.id == refund_id)
                .with_for_update()
            )
            refund = db.scalar(refund_statement)

            if refund is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Refund not found",
                )

            if refund.status not in {
                RefundStatus.REQUESTED.value,
                RefundStatus.UNDER_REVIEW.value,
            }:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Refund cannot be rejected from status {refund.status}",
                )

            if not rejection_reason.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rejection reason is required",
                )

            refund.status = RefundStatus.REJECTED
            refund.rejection_reason = rejection_reason.strip()
            refund.reviewed_by = current_user.id
            refund.reviewed_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(refund)

            return refund

        except Exception:
            db.rollback()
            raise