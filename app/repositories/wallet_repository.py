
from sqlalchemy.orm import Session

from app.models.wallet import Wallet, WalletStatus


class WalletRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        wallet_id: int,
    ) -> Wallet | None:
        return (
            db.query(Wallet)
            .filter(Wallet.id == wallet_id)
            .first()
        )

    @staticmethod
    def get_by_user_id(
        db: Session,
        user_id: int,
    ) -> Wallet | None:
        return (
            db.query(Wallet)
            .filter(Wallet.user_id == user_id)
            .first()
        )

    @staticmethod
    def create_wallet(
        db: Session,
        user_id: int,
        currency: str = "INR",
    ) -> Wallet:
        wallet = Wallet(
            user_id=user_id,
            available_balance=0,
            pending_balance=0,
            currency=currency,
            status=WalletStatus.ACTIVE,
        )

        db.add(wallet)
        db.commit()
        db.refresh(wallet)

        return wallet

    @staticmethod
    def get_all_by_user_id(
        db: Session,
        user_id: int,
    ) -> list[Wallet]:
        return (
            db.query(Wallet)
            .filter(Wallet.user_id == user_id)
            .order_by(Wallet.created_at.desc())
            .all()
        )

