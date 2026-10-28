
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.deposit import Deposit, DepositStatus
from app.models.transaction import Transaction
from app.models.transaction_limit import TransactionLimit
from app.models.user import User
from app.models.wallet import Wallet, WalletStatus
from app.repositories.deposit_repository import DepositRepository
from app.services.idempotency_service import IdempotencyService
from app.services.transaction_count_service import TransactionCountService
from app.models.notification import NotificationType
from app.services.notification_service import NotificationService


class DepositService:

    @staticmethod
    def create_deposit(
        db: Session,
        wallet_id: int,
        amount: Decimal,
        current_user: User,
        idempotency_key: str,
    ) -> Deposit:

        # Validate deposit amount.
        if not amount.is_finite() or amount <= Decimal("0"):
            raise ValueError(
                "Deposit amount must be greater than zero"
            )

        if amount != amount.quantize(Decimal("0.01")):
            raise ValueError(
                "Deposit amount can have at most 2 decimal places"
            )

        request_data = {
            "wallet_id": wallet_id,
            "amount": str(amount),
        }

        request_hash = IdempotencyService.generate_request_hash(
            request_data
        )

        try:
            # Check whether this request was already processed.
            existing_record = IdempotencyService.get_existing_record(
                db=db,
                user_id=current_user.id,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                operation="CREATE_DEPOSIT",
            )

            if existing_record is not None:
                response_body = existing_record.response_body

                if response_body is None or "id" not in response_body:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Saved deposit response is unavailable.",
                    )

                existing_deposit = db.get(
                    Deposit,
                    response_body["id"],
                )

                if existing_deposit is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Previously created deposit was not found.",
                    )

                return existing_deposit
            
            

            # Create an idempotency record.
            idempotency_record = IdempotencyService.create_record(
                db=db,
                user_id=current_user.id,
                idempotency_key=idempotency_key,
                operation="CREATE_DEPOSIT",
                request_hash=request_hash,
            )

            # Lock the wallet to prevent concurrent balance updates.
            statement = (
                select(Wallet)
                .where(Wallet.id == wallet_id)
                .with_for_update()
            )

            wallet = db.scalar(statement)

            if wallet is None:
                raise ValueError("Wallet not found")

            if (
                current_user.role == "CUSTOMER"
                and wallet.user_id != current_user.id
            ):
                raise PermissionError(
                    "You are not authorized to deposit into this wallet"
                )

            if wallet.status != WalletStatus.ACTIVE:
                raise ValueError("Wallet is not active")

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

            # Validate the user's daily transaction count.
            try:
                TransactionCountService.validate_daily_transaction_count(
                    db=db,
                    user_id=current_user.id,
                    current_transaction_type="DEPOSIT",
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "DAILY_TRANSACTION_LIMIT_EXCEEDED",
                        "message": str(exc),
                    },
                ) from exc

            # Capture the wallet balance before the deposit.
            balance_before = Decimal(
                str(wallet.available_balance)
            )

            reference_number = f"DEP-{uuid4().hex.upper()}"

            # Create deposit.
            deposit = Deposit(
                wallet_id=wallet.id,
                amount=amount,
                currency=wallet.currency,
                status=DepositStatus.PROCESSING,
                reference_number=reference_number,
            )

            db.add(deposit)
            db.flush()

            # Update wallet balance.
            wallet.available_balance = balance_before + amount

            balance_after = Decimal(
                str(wallet.available_balance)
            )

            deposit.status = DepositStatus.COMPLETED
            deposit.completed_at = datetime.now(timezone.utc)

            # Create immutable transaction ledger entry.
            ledger_entry = Transaction(
                wallet_id=wallet.id,
                transaction_type="DEPOSIT",
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                status="COMPLETED",
                reference_entity="DEPOSIT",
                reference_id=reference_number,
                description=f"Wallet deposit of {amount}",
                created_by=current_user.id,
                transaction_metadata={
                    "currency": wallet.currency,
                    "deposit_reference": reference_number,
                },
            )

            db.add(ledger_entry)
            db.flush()
            
            # Create deposit success notification.
            NotificationService.create_notification(
                           db=db,
                           user_id=wallet.user_id,
                           notification_type=NotificationType.DEPOSIT_COMPLETED,
                           title="Deposit Successful",
                            message=(
                              f"Your deposit of {amount} {wallet.currency} "
                              f"has been completed successfully. "
                              f"Reference: {reference_number}"
                            ),
                        )

            # Save the successful response for idempotent retries.
            IdempotencyService.complete_record(
                db=db,
                record=idempotency_record,
                response_body={
                    "id": deposit.id,
                    "wallet_id": deposit.wallet_id,
                    "amount": str(deposit.amount),
                    "currency": deposit.currency,
                    "status": deposit.status.value,
                    "reference_number": deposit.reference_number,
                },
            )

            # Commit deposit, balance, ledger, and idempotency together.
            db.commit()
            db.refresh(deposit)

            return deposit

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_deposit(
        db: Session,
        deposit_id: int,
        current_user: User,
    ) -> Deposit:

        deposit = DepositRepository.get_by_id(
            db=db,
            deposit_id=deposit_id,
        )

        if deposit is None:
            raise ValueError("Deposit not found")

        statement = select(Wallet).where(
            Wallet.id == deposit.wallet_id
        )

        wallet = db.scalar(statement)

        if wallet is None:
            raise ValueError("Wallet not found")

        if (
            current_user.role == "CUSTOMER"
            and wallet.user_id != current_user.id
        ):
            raise PermissionError(
                "You are not authorized to view this deposit"
            )

        return deposit

    @staticmethod
    def get_deposits(
        db: Session,
        current_user: User,
    ) -> list[Deposit]:

        statement = (
            select(Deposit)
            .join(
                Wallet,
                Deposit.wallet_id == Wallet.id,
            )
            .order_by(Deposit.created_at.desc())
        )

        # Customers can view deposits belonging only to their wallets.
        if current_user.role == "CUSTOMER":
            statement = statement.where(
                Wallet.user_id == current_user.id
            )

        deposits = db.scalars(statement).all()

        return list(deposits)



