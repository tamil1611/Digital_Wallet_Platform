
from datetime import datetime, timezone, timedelta
from app.models.transaction_limit import TransactionLimit
from decimal import Decimal
import traceback

from fastapi import HTTPException, status
from sqlalchemy import select,func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.transfer import Transfer, TransferStatus
from app.models.wallet import Wallet, WalletStatus
from app.models.transaction import Transaction
from app.models.idempotency import IdempotencyRecord

from app.repositories.transfer_repository import TransferRepository
from app.repositories.idempotency_repository import IdempotencyRepository

from app.schemas.transfer import TransferCreate
from app.services.idempotency_service import IdempotencyService
from app.services.suspicious_transaction_service import (
    SuspiciousTransactionService,
)
from app.models.notification import NotificationType
from app.services.notification_service import NotificationService
from app.services.suspicious_transaction_service import (
    SuspiciousTransactionService,
)
from app.services.audit_log_service import AuditLogService

class TransferService:
    @staticmethod
    def get_daily_transfer_total(
        db: Session,
        sender_wallet_id: int,
    ) -> Decimal:
        now = datetime.now(timezone.utc)

        today_start = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        tomorrow_start = today_start + timedelta(days=1)

        statement = select(
            func.coalesce(func.sum(Transfer.amount), 0)
        ).where(
            Transfer.sender_wallet_id == sender_wallet_id,
            Transfer.status == TransferStatus.COMPLETED,
            Transfer.completed_at >= today_start,
            Transfer.completed_at < tomorrow_start,
        )

        total = db.scalar(statement)
        return Decimal(str(total or 0))

    @staticmethod
    def create_transfer(
        db: Session,
        transfer_data: TransferCreate,
        current_user_id: int,
        idempotency_key: str,
    ) -> Transfer:

        try:
            # 1. Generate request hash.
            request_hash = IdempotencyService.generate_request_hash(
                transfer_data.model_dump(mode="json")
            )

            # 2. Check whether this key was used before.
            existing_record = IdempotencyService.get_existing_record(
                db=db,
                user_id=current_user_id,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                operation="TRANSFER",
            )

            if existing_record is not None:
                response_body = existing_record.response_body

                if response_body is None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Previous transfer response is unavailable.",
                    )

                existing_transfer = db.get(
                    Transfer,
                    response_body["id"],
                )

                if existing_transfer is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Previous transfer not found.",
                    )

                return existing_transfer

            # 3. Create idempotency record.
            idempotency_record = IdempotencyService.create_record(
                db=db,
                user_id=current_user_id,
                idempotency_key=idempotency_key,
                operation="TRANSFER",
                request_hash=request_hash,
            )

            # 4. Lock both wallets in a consistent order.
            wallet_ids = sorted(
                [
                    transfer_data.sender_wallet_id,
                    transfer_data.receiver_wallet_id,
                ]
            )

            statement = (
                select(Wallet)
                .where(Wallet.id.in_(wallet_ids))
                .order_by(Wallet.id)
                .with_for_update()
            )

            wallets = {
                wallet.id: wallet
                for wallet in db.scalars(statement).all()
            }

            sender = wallets.get(transfer_data.sender_wallet_id)
            receiver = wallets.get(transfer_data.receiver_wallet_id)

            # 5. Validate wallet existence.
            if sender is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sender wallet not found",
                )

            if receiver is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Receiver wallet not found",
                )

            # 6. Validate sender ownership.
            if sender.user_id != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not own the sender wallet",
                )

            # 7. Validate wallet status.
            if sender.status != WalletStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Sender wallet is not active",
                )

            if receiver.status != WalletStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Receiver wallet is not active",
                )

            # 8. Validate amount.
            amount = Decimal(str(transfer_data.amount))

            if not amount.is_finite() or amount <= Decimal("0.00"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transfer amount must be greater than zero",
                )

            if amount != amount.quantize(Decimal("0.01")):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transfer amount cannot have more than 2 decimal places",
                )

            # 9. Validate currency.
            if sender.currency != receiver.currency:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Sender and receiver currencies must match",
                )

            # 10. Prevent self-transfer.
            if sender.id == receiver.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot transfer to the same wallet",
                )

            # 11. Validate sufficient balance.
            if sender.available_balance < amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient wallet balance",
                )
                
                            # 11.1 Get configured transaction limits.
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

            # 11.2 Validate maximum transaction amount.
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

            # 11.3 Validate daily transfer limit.
            daily_total = TransferService.get_daily_transfer_total(
                db=db,
                sender_wallet_id=sender.id,
            )

            if daily_total + amount > limits.daily_transfer_limit:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "DAILY_TRANSFER_LIMIT_EXCEEDED",
                        "message": (
                            f"Daily transfer limit is "
                            f"{limits.daily_transfer_limit}. "
                            f"Already transferred today: {daily_total}"
                        ),
                    },
                )

                        # 12. Create transfer record.
            transfer = Transfer(
                sender_wallet_id=sender.id,
                receiver_wallet_id=receiver.id,
                amount=amount,
                currency=sender.currency,
                status=TransferStatus.PROCESSING,
            )

            TransferRepository.create(db, transfer)
            db.flush()

            # 13. Capture balances before transfer.
            sender_balance_before = sender.available_balance
            receiver_balance_before = receiver.available_balance

            
            # 14. Capture balances before transfer.
            sender_balance_before = sender.available_balance
            receiver_balance_before = receiver.available_balance

            # 15. Evaluate suspicious activity before creating ledger entries.
            risk_result = SuspiciousTransactionService.evaluate_transaction(
                db=db,
                wallet_id=sender.id,
                amount=amount,
                transaction_type="TRANSFER_DEBIT",
            )

            risk_status = risk_result["status"]
            
            print(f"Transfer risk status: {risk_status}", flush=True)



            risk_reasons = risk_result["reasons"]
            
            print(f"Transfer risk reasons: {risk_result['reasons']}", flush=True)

            # 16. Prepare the final sender ledger entry.
            sender_ledger_status = "COMPLETED"

            if risk_status == "BLOCKED":
                transfer.status = TransferStatus.FAILED
                sender_ledger_status = "FAILED"

            elif risk_status == "REVIEW_REQUIRED":
                transfer.status = TransferStatus.REVIEW_REQUIRED
                sender_ledger_status = "REVIEW_REQUIRED"

            else:
                # Complete the transfer atomically.
                sender.available_balance -= amount
                receiver.available_balance += amount

                transfer.status = TransferStatus.COMPLETED
                transfer.completed_at = datetime.now(timezone.utc)

            # 17. Insert the sender ledger only once with its final values.
            sender_ledger = Transaction(
                wallet_id=sender.id,
                transaction_type="TRANSFER_DEBIT",
                amount=amount,
                balance_before=sender_balance_before,
                balance_after=sender.available_balance,
                status=sender_ledger_status,
                reference_entity="TRANSFER",
                reference_id=str(transfer.id),
                description=f"Transfer sent to wallet {receiver.id}",
                created_by=current_user_id,
                transaction_metadata={
                    "transfer_id": transfer.id,
                    "direction": "DEBIT",
                    "currency": sender.currency,
                    "risk_status": risk_status,
                    "risk_reasons": risk_reasons,
                },
            )

            db.add(sender_ledger)
            db.flush()

           
                    # 18. Create suspicious alert and notification.
            if risk_status in ("BLOCKED", "REVIEW_REQUIRED"):
                from app.models.suspicious_transaction import (
                    SuspiciousTransactionAlert,
                )

                alert = SuspiciousTransactionAlert(
                    transaction_id=sender_ledger.id,
                    wallet_id=sender.id,
                    amount=amount,
                    status=risk_status,
                    risk_reason=", ".join(risk_reasons),
                )
                db.add(alert)

                NotificationService.create_notification(
                    db=db,
                    user_id=sender.user_id,
                    notification_type=(
                        NotificationType.SUSPICIOUS_TRANSACTION_DETECTED
                    ),
                    title="Suspicious Transaction Detected",
                    message=(
                        f"Your transfer of {amount} {sender.currency} "
                        f"was flagged for review. "
                        f"Reasons: {', '.join(risk_reasons)}. "
                        f"Status: {risk_status}."
                    ),
                )



            # 19. Create receiver ledger and notifications only on success.
            if risk_status == "NORMAL":
                print("TRANSFER NOTIFICATION BLOCK EXECUTED", flush=True)
                receiver_ledger = Transaction(
                    wallet_id=receiver.id,
                    transaction_type="TRANSFER_CREDIT",
                    amount=amount,
                    balance_before=receiver_balance_before,
                    balance_after=receiver.available_balance,
                    status="COMPLETED",
                    reference_entity="TRANSFER",
                    reference_id=str(transfer.id),
                    description=(
                        f"Transfer received from wallet {sender.id}"
                    ),
                    created_by=current_user_id,
                    transaction_metadata={
                        "transfer_id": transfer.id,
                        "direction": "CREDIT",
                        "currency": receiver.currency,
                    },
                )

                db.add(receiver_ledger)
                
                print(f"Creating sender notification for user {sender.user_id}", flush=True)

                # Notify sender.
                NotificationService.create_notification(
                    db=db,
                    user_id=sender.user_id,
                    notification_type=NotificationType.TRANSFER_COMPLETED,
                    title="Transfer Successful",
                    message=(
                        f"Your transfer of {amount} {sender.currency} "
                        f"to wallet {receiver.id} was completed successfully."
                    ),
                )
                
                print(f"Creating receiver notification for user {receiver.user_id}", flush=True)

                # Notify receiver.
                NotificationService.create_notification(
                    db=db,
                    user_id=receiver.user_id,
                    notification_type=NotificationType.TRANSFER_RECEIVED,
                    title="Money Received",
                    message=(
                        f"You received {amount} {receiver.currency} "
                        f"from wallet {sender.id}."
                    ),
                )

            
            # 20. Flush all records before committing.
            db.flush()
            db.refresh(transfer)
            
                        # 20.1 Create transfer audit log.
            audit_action = {
                TransferStatus.COMPLETED: "TRANSFER_COMPLETED",
                TransferStatus.FAILED: "TRANSFER_FAILED",
                TransferStatus.REVIEW_REQUIRED: "TRANSFER_REVIEW_REQUIRED",
            }.get(transfer.status, "TRANSFER_CREATED")

            AuditLogService.create_log(
                db=db,
                user_id=current_user_id,
                action=audit_action,
                entity="TRANSFER",
                entity_id=transfer.id,
                metadata={
                    "sender_wallet_id": sender.id,
                    "receiver_wallet_id": receiver.id,
                    "amount": str(amount),
                    "currency": sender.currency,
                    "status": transfer.status.value,
                },
            )
            
             # 20.2 Save the idempotency response.
            IdempotencyService.complete_record(
                db=db,
                record=idempotency_record,
                response_body={
                    "id": transfer.id,
                },
            )

            

            # Commit transfer, ledger, balances and notifications together.
            db.commit()
            db.refresh(transfer)

            print(
                f"Transfer {transfer.id} committed successfully.",
                flush=True,
            )

            return transfer

        except HTTPException:
            db.rollback()
            raise

        except IntegrityError as exc:
            db.rollback()

            # A concurrent request may have claimed the same key.
            existing_record = IdempotencyRepository.get_by_key(
                db=db,
                user_id=current_user_id,
                idempotency_key=idempotency_key,
            )

            if existing_record is not None:
                if existing_record.operation != "TRANSFER":
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "This Idempotency-Key was already used "
                            "for another operation."
                        ),
                    ) from exc

                request_hash = IdempotencyService.generate_request_hash(
                    transfer_data.model_dump(mode="json")
                )

                if existing_record.request_hash != request_hash:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "This Idempotency-Key was already used "
                            "with a different request."
                        ),
                    ) from exc

                if (
                    existing_record.status == "COMPLETED"
                    and existing_record.response_body
                ):
                    existing_transfer = db.get(
                        Transfer,
                        existing_record.response_body["id"],
                    )

                    if existing_transfer is not None:
                        return existing_transfer

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Duplicate Idempotency-Key. "
                    "Please retry the request."
                ),
            ) from exc

        except Exception as exc:
            db.rollback()

            print("========== TRANSFER ERROR ==========", flush=True)
            traceback.print_exc()
            print("=====================================", flush=True)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Transfer failed. "
                    "No balance changes were committed."
                ),
            ) from exc
            
    @staticmethod
    def get_transfer(
        db: Session,
        transfer_id: int,
        current_user_id: int,
    ) -> Transfer:
        transfer = db.get(Transfer, transfer_id)

        if transfer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found",
            )

        sender_wallet = db.get(Wallet, transfer.sender_wallet_id)
        receiver_wallet = db.get(Wallet, transfer.receiver_wallet_id)

        if (
            sender_wallet is None
            or receiver_wallet is None
            or (
                sender_wallet.user_id != current_user_id
                and receiver_wallet.user_id != current_user_id
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this transfer",
            )

        return transfer
    
    @staticmethod
    def get_transfers(
        db: Session,
        current_user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Transfer]:

        # Get all wallet IDs belonging to the current user.
        user_wallet_ids = select(Wallet.id).where(
            Wallet.user_id == current_user_id
        )

        # Fetch transfers sent or received by the user.
        statement = (
            select(Transfer)
            .where(
                (
                    Transfer.sender_wallet_id.in_(user_wallet_ids)
                )
                |
                (
                    Transfer.receiver_wallet_id.in_(user_wallet_ids)
                )
            )
            .order_by(Transfer.id.desc())
            .offset(skip)
            .limit(limit)
        )

        transfers = db.scalars(statement).all()

        return list(transfers)

    
    
    @staticmethod
    def cancel_transfer(
        db: Session,
        transfer_id: int,
        current_user_id: int,
    ) -> Transfer:
        transfer = db.get(Transfer, transfer_id)

        if transfer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found",
            )

        sender_wallet = db.get(
            Wallet,
            transfer.sender_wallet_id,
        )

        if (
            sender_wallet is None
            or sender_wallet.user_id != current_user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to cancel this transfer",
            )

        if transfer.status != TransferStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending transfers can be cancelled",
            )

        try:
            transfer.status = TransferStatus.CANCELLED

            AuditLogService.create_log(
                db=db,
                user_id=current_user_id,
                action="TRANSFER_CANCELLED",
                entity="TRANSFER",
                entity_id=transfer.id,
                metadata={
                    "status": transfer.status.value,
                },
            )

            db.commit()
            db.refresh(transfer)

            return transfer

        except Exception as exc:
            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel transfer",
            ) from exc