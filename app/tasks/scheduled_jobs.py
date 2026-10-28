from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func

from app.database import SessionLocal
from app.models.transfer import Transfer, TransferStatus
from app.models.transaction import Transaction
from app.models.suspicious_transaction import (
    SuspiciousStatus,
    SuspiciousTransactionAlert,
)

scheduler = BackgroundScheduler(timezone="Asia/Kolkata")


def daily_transaction_limit_reset():
    print("Running daily transaction limit reset...")


def pending_transaction_cleanup():
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

    db = SessionLocal()

    try:
        statement = select(func.count(Transfer.id)).where(
            Transfer.status == TransferStatus.PENDING,
            Transfer.created_at < cutoff_time,
        )

        pending_count = db.scalar(statement) or 0

        print(
            f"Pending cleanup scan completed. "
            f"Transfers older than 24 hours: {pending_count}",
            flush=True,
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def suspicious_transaction_scanning():
    print("Suspicious transaction scanning started.", flush=True)

    """Scan eligible transactions for suspicious activity."""

    db = SessionLocal()

    scanned_count = 0
    alert_count = 0

    try:
        statement = (
            select(Transaction)
            .where(
                Transaction.status.in_(
                    ["PROCESSING", "REVIEW_REQUIRED"]
                )
            )
            .order_by(Transaction.id)
        )

        transactions = db.scalars(statement).all()

        for transaction in transactions:
            scanned_count += 1

            # Check whether an alert already exists.
            existing_alert = db.scalar(
                select(SuspiciousTransactionAlert.id).where(
                    SuspiciousTransactionAlert.transaction_id
                    == transaction.id
                ).limit(1)
            )

            if existing_alert is not None:
                continue

            # Do not create alerts for normal transactions.
            if transaction.status != "REVIEW_REQUIRED":
                continue

            alert = SuspiciousTransactionAlert(
                transaction_id=transaction.id,
                wallet_id=transaction.wallet_id,
                amount=transaction.amount,
                status=SuspiciousStatus.REVIEW_REQUIRED.value,
                risk_reason=(
                    transaction.description
                    or "TRANSACTION_REQUIRES_REVIEW"
                ),
            )

            db.add(alert)
            alert_count += 1

        db.commit()

        print(
            "Suspicious transaction scan completed. "
            f"Scanned: {scanned_count}, "
            f"New alerts: {alert_count}",
            flush=True,
        )

    except Exception:
        db.rollback()
        print(
            "Suspicious transaction scanning failed.",
            flush=True,
        )
        raise

    finally:
        db.close()


def daily_wallet_summary():
    print("Generating daily wallet summary...")



def failed_transaction_retry():
    """Find eligible failed transfers and report retry eligibility."""
    print("Failed transaction retry job started.", flush=True)

    db = SessionLocal()

    try:
        max_retries = 3

        statement = (
            select(Transfer)
            .where(
                Transfer.status == TransferStatus.FAILED,
                Transfer.retry_count < max_retries,
            )
            .order_by(Transfer.created_at)
        )

        failed_transfers = db.scalars(statement).all()

        eligible_count = 0

        for transfer in failed_transfers:
            # Do not automatically retry a transfer unless its failure
            # is explicitly known to be transient and safe to retry.
            print(
                f"Transfer {transfer.id} needs retry eligibility review. "
                f"Retry count: {transfer.retry_count}. "
                "No automatic retry performed.",
                flush=True,
            )
            eligible_count += 1

        print(
            f"Failed transfer scan completed. "
            f"Transfers reviewed: {eligible_count}. "
            "Automatic retries: 0.",
            flush=True,
        )

    except Exception:
        db.rollback()
        print("Failed transaction retry job failed.", flush=True)
        raise

    finally:
        db.close()




def daily_transaction_report():
    """Generate a daily summary of wallet transactions."""
    print("Generating daily transaction report...", flush=True)

    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        statement = (
            select(
                Transaction.status,
                func.count(Transaction.id).label("transaction_count"),
                func.coalesce(func.sum(Transaction.amount), 0).label(
                    "total_amount"
                ),
            )
            .where(
                Transaction.created_at >= start_of_day,
                Transaction.created_at <= now,
            )
            .group_by(Transaction.status)
            .order_by(Transaction.status)
        )

        results = db.execute(statement).all()

        print("Daily transaction report:", flush=True)
        print(f"Report period: {start_of_day} to {now}", flush=True)

        if not results:
            print("No transactions found for this period.", flush=True)

        for row in results:
            print(
                f"Status: {row.status}, "
                f"Count: {row.transaction_count}, "
                f"Total amount: {row.total_amount}",
                flush=True,
            )

        print("Daily transaction report completed.", flush=True)

    except Exception:
        db.rollback()
        print("Daily transaction report failed.", flush=True)
        raise

    finally:
        db.close()
        
        




def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(
        daily_transaction_limit_reset,
        trigger="cron",
        hour=0,
        minute=0,
        id="daily_transaction_limit_reset",
        replace_existing=True,
    )

    scheduler.add_job(
        pending_transaction_cleanup,
        trigger="interval",
        minutes=5,
        id="pending_transaction_cleanup",
        replace_existing=True,
    )

    scheduler.add_job(
        suspicious_transaction_scanning,
        trigger="interval",
        minutes=10,
        id="suspicious_transaction_scanning",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )

    scheduler.add_job(
        daily_wallet_summary,
        trigger="cron",
        hour=23,
        minute=55,
        id="daily_wallet_summary",
        replace_existing=True,
    )

    scheduler.add_job(
        failed_transaction_retry,
        trigger="interval",
        minutes=5,
        id="failed_transaction_retry",
        replace_existing=True,
    )

    scheduler.add_job(
        daily_transaction_report,
        trigger="cron",
        hour=23,
        minute=59,
        id="daily_transaction_report",
        replace_existing=True,
    )

    scheduler.start()
    print("Scheduled jobs started successfully.")