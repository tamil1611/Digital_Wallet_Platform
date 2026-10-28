

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.wallet_repository import WalletRepository


class TransactionService:

    @staticmethod
    def get_transaction(
        db: Session,
        transaction_id: int,
        current_user: User,
    ) -> Transaction:
        transaction = TransactionRepository.get_by_id(
            db=db,
            transaction_id=transaction_id,
        )

        if transaction is None:
            raise ValueError("Transaction not found")

        wallet = WalletRepository.get_by_id(
            db=db,
            wallet_id=transaction.wallet_id,
        )

        if wallet is None:
            raise ValueError("Wallet not found")

        if (
            current_user.role == "CUSTOMER"
            and wallet.user_id != current_user.id
        ):
            raise PermissionError(
                "You are not authorized to access this transaction"
            )

        return transaction

    @staticmethod
    def get_wallet_transactions(
        db: Session,
        wallet_id: int,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Transaction]:
        wallet = WalletRepository.get_by_id(
            db=db,
            wallet_id=wallet_id,
        )

        if wallet is None:
            raise ValueError("Wallet not found")

        if (
            current_user.role == "CUSTOMER"
            and wallet.user_id != current_user.id
        ):
            raise PermissionError(
                "You are not authorized to access these transactions"
            )

        return TransactionRepository.get_by_wallet_id(
            db=db,
            wallet_id=wallet_id,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    def get_transaction_history(
        db: Session,
        current_user: User,
        *,
        wallet_id: int | None = None,
        transaction_type: str | None = None,
        transaction_status: str | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        if page < 1:
            raise ValueError("Page must be at least 1")

        if not 1 <= page_size <= 100:
            raise ValueError("Page size must be between 1 and 100")

        if (
            min_amount is not None
            and max_amount is not None
            and min_amount > max_amount
        ):
            raise ValueError(
                "min_amount cannot be greater than max_amount"
            )

        if from_date is not None and to_date is not None:
            if from_date > to_date:
                raise ValueError(
                    "from_date cannot be later than to_date"
                )

        allowed_types = {
            "DEPOSIT",
            "WITHDRAWAL",
            "TRANSFER_DEBIT",
            "TRANSFER_CREDIT",
            "REFUND",
            "FEE",
            "ADJUSTMENT",
            "REVERSAL",
        }

        if (
            transaction_type is not None
            and transaction_type.upper() not in allowed_types
        ):
            raise ValueError("Invalid transaction type")

        allowed_statuses = {
            "PENDING",
            "PROCESSING",
            "REVIEW_REQUIRED",
            "COMPLETED",
            "FAILED",
            "CANCELLED",
        }

        if (
            transaction_status is not None
            and transaction_status.upper() not in allowed_statuses
        ):
            raise ValueError("Invalid transaction status")

        if sort_by not in {
            "id",
            "amount",
            "created_at",
            "status",
            "transaction_type",
        }:
            raise ValueError("Invalid sort_by field")

        if sort_order.lower() not in {"asc", "desc"}:
            raise ValueError("sort_order must be asc or desc")

        # Restrict customers to their own wallets.
        if current_user.role == "CUSTOMER":
            if wallet_id is not None:
                wallet = WalletRepository.get_by_id(
                    db=db,
                    wallet_id=wallet_id,
                )

                if wallet is None:
                    raise ValueError("Wallet not found")

                if wallet.user_id != current_user.id:
                    raise PermissionError(
                        "You are not authorized to access these transactions"
                    )
            else:
                # Do not allow customers to query other users' transactions.
                # The repository is extended below to support owner filtering.
                pass

        # Convert date filters to UTC boundaries.
        from_datetime = (
            datetime.combine(
                from_date,
                time.min,
                tzinfo=timezone.utc,
            )
            if from_date is not None
            else None
        )

        to_datetime = (
            datetime.combine(
                to_date + timedelta(days=1),
                time.min,
                tzinfo=timezone.utc,
            )
            if to_date is not None
            else None
        )

        transactions, total = (
            TransactionRepository.get_transaction_history(
                db=db,
                wallet_id=wallet_id,
                owner_user_id=(
                       current_user.id
                       if current_user.role == "CUSTOMER"
                       else None
                ),
                transaction_type=transaction_type,
                transaction_status=transaction_status,
                min_amount=min_amount,
                max_amount=max_amount,
                from_date=from_datetime,
                to_date=to_datetime,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order.lower(),
                page=page,
                page_size=page_size,
            )
        )

        return {
            "items": transactions,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (
                (total + page_size - 1) // page_size
            ),
        }

    @staticmethod
    def create_transaction(
        db: Session,
        current_user: User,
        wallet_id: int,
        transaction_type: str,
        amount: Decimal,
        description: str | None = None,
    ) -> Transaction:
        if amount <= Decimal("0.00"):
            raise ValueError(
                "Transaction amount must be greater than zero"
            )

        wallet = WalletRepository.get_by_id(
            db=db,
            wallet_id=wallet_id,
        )

        if wallet is None:
            raise ValueError("Wallet not found")

        if wallet.user_id != current_user.id:
            raise PermissionError(
                "You are not authorized to use this wallet"
            )

        if wallet.status != "ACTIVE":
            raise ValueError("Wallet is not active")

        allowed_types = {
            "DEPOSIT",
            "WITHDRAWAL",
            "TRANSFER",
            "REFUND",
        }

        if transaction_type not in allowed_types:
            raise ValueError("Invalid transaction type")

        return TransactionRepository.create(
            db=db,
            wallet_id=wallet_id,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
        )

