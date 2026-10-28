
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.transaction_limit import TransactionLimit

from app.core.config import settings
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet, WalletStatus
from app.models.withdrawal import Withdrawal, WithdrawalStatus
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.withdrawal_repository import WithdrawalRepository
from app.services.idempotency_service import IdempotencyService
from app.models.notification import NotificationType
from app.services.notification_service import NotificationService
from app.models.audit_log import AuditLog

class WithdrawalService:

    @staticmethod
    def create_withdrawal(
        db: Session,
        wallet_id: int,
        amount: Decimal,
        current_user: User,
        idempotency_key: str,
    ) -> Withdrawal:

        if not amount.is_finite() or amount <= Decimal("0"):
            raise ValueError(
                "Withdrawal amount must be greater than zero"
            )

        if amount != amount.quantize(Decimal("0.01")):
            raise ValueError(
                "Withdrawal amount can have at most 2 decimal places"
            )

        request_hash = IdempotencyService.generate_request_hash(
            {
                "wallet_id": wallet_id,
                "amount": str(amount),
            }
        )

        try:
            existing_record = IdempotencyService.get_existing_record(
                db=db,
                user_id=current_user.id,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                operation="CREATE_WITHDRAWAL",
            )

            if existing_record is not None:
                response_body = existing_record.response_body

                if response_body is None or "id" not in response_body:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Saved withdrawal response is unavailable.",
                    )

                existing_withdrawal = db.get(
                    Withdrawal,
                    response_body["id"],
                )

                if existing_withdrawal is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Previously created withdrawal was not found.",
                    )

                return existing_withdrawal

            idempotency_record = IdempotencyService.create_record(
                db=db,
                user_id=current_user.id,
                idempotency_key=idempotency_key,
                operation="CREATE_WITHDRAWAL",
                request_hash=request_hash,
            )

            wallet_statement = (
                select(Wallet)
                .where(Wallet.id == wallet_id)
                .with_for_update()
            )
            wallet = db.scalar(wallet_statement)

            if wallet is None:
                raise ValueError("Wallet not found")

            if (
                current_user.role == "CUSTOMER"
                and wallet.user_id != current_user.id
            ):
                raise PermissionError(
                    "You are not authorized to withdraw from this wallet"
                )

            if wallet.status != WalletStatus.ACTIVE:
                raise ValueError("Wallet is not active")

            balance_before = Decimal(str(wallet.available_balance))

            if balance_before < amount:
                raise ValueError("Insufficient wallet balance")

                         # Get admin-configured transaction limits.
            limits = db.scalar(
                select(TransactionLimit)
                .order_by(TransactionLimit.id)
                .limit(1)
            )

            if limits is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Transaction limits are not configured",
                )

            # Validate maximum transaction amount.
            if amount > limits.max_transaction_amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "MAX_TRANSACTION_AMOUNT_EXCEEDED",
                        "message": (
                            f"Maximum transaction amount is "
                            f"{limits.max_transaction_amount}"
                        ),
                    },
                )

            # Calculate today's UTC withdrawal total.
            now = datetime.now(timezone.utc)

            day_start = datetime.combine(
                now.date(),
                time.min,
                tzinfo=timezone.utc,
            )
            day_end = day_start + timedelta(days=1)

            daily_statement = select(
                func.coalesce(func.sum(Withdrawal.amount), 0)
            ).where(
                Withdrawal.wallet_id == wallet_id,
                Withdrawal.status == WithdrawalStatus.COMPLETED,
                Withdrawal.completed_at >= day_start,
                Withdrawal.completed_at < day_end,
            )

            daily_total = Decimal(
                str(db.scalar(daily_statement) or 0)
            )

            # Validate configured daily withdrawal limit.
            if daily_total + amount > limits.daily_withdrawal_limit:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "DAILY_WITHDRAWAL_LIMIT_EXCEEDED",
                        "message": (
                            f"Daily withdrawal limit is "
                            f"{limits.daily_withdrawal_limit}. "
                            f"Already withdrawn today: {daily_total}"
                        ),
                    },
                )

            reference_number = f"WDR-{uuid4().hex.upper()}"

            withdrawal = Withdrawal(
                wallet_id=wallet.id,
                amount=amount,
                currency=wallet.currency,
                status=WithdrawalStatus.PROCESSING,
                reference_number=reference_number,
                created_by=current_user.id,
            )

            WithdrawalRepository.create(
                db=db,
                withdrawal=withdrawal,
            )

            wallet.available_balance = balance_before - amount
            balance_after = Decimal(str(wallet.available_balance))

            withdrawal.status = WithdrawalStatus.COMPLETED
            withdrawal.completed_at = now

            ledger_entry = Transaction(
                wallet_id=wallet.id,
                transaction_type="WITHDRAWAL",
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                status="COMPLETED",
                reference_entity="WITHDRAWAL",
                reference_id=reference_number,
                description=f"Wallet withdrawal of {amount}",
                created_by=current_user.id,
                transaction_metadata={
                    "currency": wallet.currency,
                    "withdrawal_reference": reference_number,
                },
            )

            db.add(ledger_entry)
            db.flush()
            
            # Create withdrawal audit log.
            audit_log = AuditLog(
               user_id=current_user.id,
                action="WITHDRAWAL_CREATED",
                entity="WITHDRAWAL",
                entity_id=str(withdrawal.id),
                 metadata={
                   "wallet_id": wallet.id,
                   "amount": str(amount),
                   "currency": wallet.currency,
                   "status": withdrawal.status.value,
                   "reference_number": reference_number,
                 },
            )

            db.add(audit_log)
            db.flush()
            
            
            # Create withdrawal success notification.
            NotificationService.create_notification(
               db=db,
               user_id=wallet.user_id,
               notification_type=NotificationType.WITHDRAWAL_COMPLETED,
               title="Withdrawal Successful",
               message=(
                 f"Your withdrawal of {amount} {wallet.currency} "
                  f"has been completed successfully. "
                  f"Reference: {reference_number}"
                ),
            )

            IdempotencyService.complete_record(
                db=db,
                record=idempotency_record,
                response_body={
                    "id": withdrawal.id,
                    "wallet_id": withdrawal.wallet_id,
                    "amount": str(withdrawal.amount),
                    "currency": withdrawal.currency,
                    "status": withdrawal.status.value,
                    "reference_number": withdrawal.reference_number,
                },
            )

            db.commit()
            db.refresh(withdrawal)

            return withdrawal

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_withdrawal(
        db: Session,
        withdrawal_id: int,
        current_user: User,
    ) -> Withdrawal:

        withdrawal = WithdrawalRepository.get_by_id(
            db=db,
            withdrawal_id=withdrawal_id,
        )

        if withdrawal is None:
            raise ValueError("Withdrawal not found")

        wallet = db.get(Wallet, withdrawal.wallet_id)

        if wallet is None:
            raise ValueError("Wallet not found")

        if (
            current_user.role == "CUSTOMER"
            and wallet.user_id != current_user.id
        ):
            raise PermissionError(
                "You are not authorized to view this withdrawal"
            )

        return withdrawal

    @staticmethod
    def get_withdrawals(
        db: Session,
        current_user: User,
    ) -> list[Withdrawal]:

        statement = (
            select(Withdrawal)
            .join(Wallet, Withdrawal.wallet_id == Wallet.id)
            .order_by(Withdrawal.created_at.desc())
        )

        if current_user.role == "CUSTOMER":
            statement = statement.where(
                Wallet.user_id == current_user.id
            )

        return list(db.scalars(statement).all())

    @staticmethod
    def cancel_withdrawal(
        db: Session,
        withdrawal_id: int,
        current_user: User,
    ) -> Withdrawal:

        try:
            statement = (
                select(Withdrawal)
                .where(Withdrawal.id == withdrawal_id)
                .with_for_update()
            )
            withdrawal = db.scalar(statement)

            if withdrawal is None:
                raise ValueError("Withdrawal not found")

            wallet_statement = (
                select(Wallet)
                .where(Wallet.id == withdrawal.wallet_id)
                .with_for_update()
            )
            wallet = db.scalar(wallet_statement)

            if wallet is None:
                raise ValueError("Wallet not found")

            if (
                current_user.role == "CUSTOMER"
                and wallet.user_id != current_user.id
            ):
                raise PermissionError(
                    "You are not authorized to cancel this withdrawal"
                )

            if withdrawal.status != WithdrawalStatus.PENDING:
                raise ValueError(
                    "Only pending withdrawals can be cancelled"
                )

            withdrawal.status = WithdrawalStatus.CANCELLED

            db.commit()
            db.refresh(withdrawal)

            return withdrawal

        except Exception:
            db.rollback()
            raise

