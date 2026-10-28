

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.refund import Refund, RefundStatus
from app.models.suspicious_transaction import SuspiciousTransactionAlert
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet, WalletStatus
from app.models.deposit import Deposit
from app.models.transfer import Transfer
from app.models.withdrawal import Withdrawal


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get("/admin")
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only SUPER_ADMIN and ADMIN can access this endpoint.
    if current_user.role not in {"SUPER_ADMIN", "ADMIN"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the admin dashboard.",
        )

    # Today's date range in UTC.
    now = datetime.now(timezone.utc)
    start_of_day = datetime.combine(
        now.date(),
        time.min,
        tzinfo=timezone.utc,
    )
    start_of_next_day = start_of_day + timedelta(days=1)

    # Total registered users.
    total_users = db.query(func.count(User.id)).scalar() or 0

    # Active wallets.
    active_wallets = (
        db.query(func.count(Wallet.id))
        .filter(Wallet.status == WalletStatus.ACTIVE)
        .scalar()
        or 0
    )

    # Total balance across all active wallets.
    total_wallet_balance = (
        db.query(func.coalesce(func.sum(Wallet.available_balance), 0))
        .filter(Wallet.status == WalletStatus.ACTIVE)
        .scalar()
        or Decimal("0.00")
    )

    # Today's transaction count.
    todays_transactions = (
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.created_at >= start_of_day,
            Transaction.created_at < start_of_next_day,
        )
        .scalar()
        or 0
    )

    # Today's transaction volume.
    todays_transaction_volume = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.created_at >= start_of_day,
            Transaction.created_at < start_of_next_day,
            Transaction.status == "COMPLETED",
        )
        .scalar()
        or Decimal("0.00")
    )

    # Failed transactions.
    failed_transactions = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.status == "FAILED")
        .scalar()
        or 0
    )

    # Suspicious transactions awaiting review or blocked.
    suspicious_transactions = (
        db.query(func.count(SuspiciousTransactionAlert.id))
        .filter(
            SuspiciousTransactionAlert.status.in_(
                ["REVIEW_REQUIRED", "BLOCKED"]
            )
        )
        .scalar()
        or 0
    )

    return {
        "total_users": total_users,
        "active_wallets": active_wallets,
        "total_wallet_balance": total_wallet_balance,
        "todays_transactions": todays_transactions,
        "todays_transaction_volume": todays_transaction_volume,
        "failed_transactions": failed_transactions,
        "suspicious_transactions": suspicious_transactions,
    }

@router.get("/support")
def get_support_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only Support Agents can access this dashboard.
    if current_user.role != "SUPPORT_AGENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the support dashboard.",
        )

    # Pending reviews.
    pending_reviews = (
        db.query(func.count(SuspiciousTransactionAlert.id))
        .filter(
            SuspiciousTransactionAlert.status == "REVIEW_REQUIRED"
        )
        .scalar()
        or 0
    )

    # Suspicious transactions awaiting review or blocked.
    suspicious_transactions = (
        db.query(func.count(SuspiciousTransactionAlert.id))
        .filter(
            SuspiciousTransactionAlert.status.in_(
                ["REVIEW_REQUIRED", "BLOCKED"]
            )
        )
        .scalar()
        or 0
    )

    # Failed transactions.
    failed_transactions = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.status == "FAILED")
        .scalar()
        or 0
    )

    # Refund requests awaiting action.
    refund_requests = (
        db.query(func.count(Refund.id))
        .filter(
            Refund.status.in_(
                [
                    RefundStatus.REQUESTED.value,
                    RefundStatus.UNDER_REVIEW.value,
                ]
            )
        )
        .scalar()
        or 0
    )

    # Frozen wallets.
    frozen_wallets = (
        db.query(func.count(Wallet.id))
        .filter(Wallet.status == WalletStatus.FROZEN)
        .scalar()
        or 0
    )

    return {
        "pending_reviews": pending_reviews,
        "suspicious_transactions": suspicious_transactions,
        "failed_transactions": failed_transactions,
        "refund_requests": refund_requests,
        "frozen_wallets": frozen_wallets,
    }

@router.get("/customer")
def get_customer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only customers can access this dashboard.
    if current_user.role != "CUSTOMER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the customer dashboard.",
        )

    # Get the customer's wallets.
    wallets = (
        db.query(Wallet)
        .filter(Wallet.user_id == current_user.id)
        .all()
    )

    wallet_ids = [wallet.id for wallet in wallets]

    # Calculate the customer's total available balance.
    wallet_balance = sum(
        (wallet.available_balance for wallet in wallets),
        Decimal("0.00"),
    )

    # Get the customer's recent transactions.
    recent_transactions = []

    if wallet_ids:
        transactions = (
            db.query(Transaction)
            .filter(Transaction.wallet_id.in_(wallet_ids))
            .order_by(Transaction.created_at.desc())
            .limit(5)
            .all()
        )

        recent_transactions = [
            {
                "id": transaction.id,
                "transaction_type": transaction.transaction_type,
                "amount": transaction.amount,
                "status": transaction.status,
                "created_at": transaction.created_at,
            }
            for transaction in transactions
        ]

    # Calculate total deposits.
    total_deposits = (
        db.query(func.coalesce(func.sum(Deposit.amount), 0))
        .filter(Deposit.wallet_id.in_(wallet_ids))
        .scalar()
        or Decimal("0.00")
    ) if wallet_ids else Decimal("0.00")

    # Calculate total transfers sent.
    total_transfers = (
        db.query(func.coalesce(func.sum(Transfer.amount), 0))
        .filter(Transfer.sender_wallet_id.in_(wallet_ids))
        .filter(Transfer.status == "COMPLETED")
        .scalar()
        or Decimal("0.00")
    ) if wallet_ids else Decimal("0.00")

    # Calculate total withdrawals.
    total_withdrawals = (
        db.query(func.coalesce(func.sum(Withdrawal.amount), 0))
        .filter(Withdrawal.wallet_id.in_(wallet_ids))
        .filter(Withdrawal.status == "COMPLETED")
        .scalar()
        or Decimal("0.00")
    ) if wallet_ids else Decimal("0.00")

    # Count pending transactions.
    pending_transactions = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.wallet_id.in_(wallet_ids))
        .filter(
            Transaction.status.in_(
                ["PENDING", "PROCESSING", "REVIEW_REQUIRED"]
            )
        )
        .scalar()
        or 0
    ) if wallet_ids else 0

    return {
        "wallet_balance": wallet_balance,
        "recent_transactions": recent_transactions,
        "total_deposits": total_deposits,
        "total_transfers": total_transfers,
        "total_withdrawals": total_withdrawals,
        "pending_transactions": pending_transactions,
    }