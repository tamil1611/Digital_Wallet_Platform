
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.wallet import Wallet


class TransactionRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        transaction_id: int,
    ) -> Transaction | None:
        return (
            db.query(Transaction)
            .filter(Transaction.id == transaction_id)
            .first()
        )

    @staticmethod
    def get_by_wallet_id(
        db: Session,
        wallet_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Transaction]:
        return (
            db.query(Transaction)
            .filter(Transaction.wallet_id == wallet_id)
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_transaction_history(
        db: Session,
        *,
        wallet_id: int | None = None,
        owner_user_id: int | None = None,
        transaction_type: str | None = None,
        transaction_status: str | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
       
    ) -> tuple[list[Transaction], int]:

        query = db.query(Transaction)
        
        if owner_user_id is not None:
            query = (
                query
                .join(
                    Wallet,
                    Transaction.wallet_id == Wallet.id,
                )
                .filter(Wallet.user_id == owner_user_id)
            )

        if wallet_id is not None:
            query = query.filter(
                Transaction.wallet_id == wallet_id
            )

        if transaction_type:
            query = query.filter(
                Transaction.transaction_type
                == transaction_type.upper()
            )

        if transaction_status:
            query = query.filter(
                Transaction.status == transaction_status.upper()
            )

        if min_amount is not None:
            query = query.filter(
                Transaction.amount >= min_amount
            )

        if max_amount is not None:
            query = query.filter(
                Transaction.amount <= max_amount
            )

        if from_date is not None:
            query = query.filter(
                Transaction.created_at >= from_date
            )

        if to_date is not None:
            query = query.filter(
                Transaction.created_at < to_date
            )

        if search:
            search_term = f"%{search.strip()}%"

            query = query.filter(
                or_(
                    Transaction.description.ilike(search_term),
                    Transaction.reference_id.ilike(search_term),
                    Transaction.reference_entity.ilike(search_term),
                )
            )

        total = query.order_by(None).count()

        sortable_columns = {
            "id": Transaction.id,
            "amount": Transaction.amount,
            "created_at": Transaction.created_at,
            "status": Transaction.status,
            "transaction_type": Transaction.transaction_type,
        }

        sort_column = sortable_columns[sort_by]

        if sort_order == "desc":
            query = query.order_by(
                sort_column.desc(),
                Transaction.id.desc(),
            )
        else:
            query = query.order_by(
                sort_column.asc(),
                Transaction.id.asc(),
            )

        transactions = (
            query
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return transactions, total

    @staticmethod
    def create(
        db: Session,
        wallet_id: int,
        transaction_type: str,
        amount: Decimal,
        description: str | None = None,
        reference_id: str | None = None,
    ) -> Transaction:
        transaction = Transaction(
            wallet_id=wallet_id,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            reference_id=reference_id,
            status="PENDING",
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return transaction

