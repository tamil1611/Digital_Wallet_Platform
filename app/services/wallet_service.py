
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.wallet import Wallet, WalletStatus
from app.repositories.wallet_repository import WalletRepository
from app.schemas.wallet import WalletUpdate
from app.models.notification import NotificationType
from app.services.notification_service import NotificationService


class WalletService:

    @staticmethod
    def create_wallet(
        db: Session,
        current_user: User,
        currency: str = "INR",
    ) -> Wallet:
        # Check whether the user already has a wallet.
        existing_wallet = WalletRepository.get_by_user_id(
            db=db,
            user_id=current_user.id,
        )

        if existing_wallet is not None:
            raise ValueError("User already has a wallet")

        # Create a wallet for the authenticated user.
        return WalletRepository.create_wallet(
            db=db,
            user_id=current_user.id,
            currency=currency,
        )

    @staticmethod
    def get_wallet(
        db: Session,
        wallet_id: int,
        current_user: User,
    ) -> Wallet:
        wallet = WalletRepository.get_by_id(
            db=db,
            wallet_id=wallet_id,
        )

        if wallet is None:
            raise ValueError("Wallet not found")

        # Customers can access only their own wallets.
        if (
            current_user.role == "CUSTOMER"
            and wallet.user_id != current_user.id
        ):
            raise PermissionError(
                "You are not authorized to access this wallet"
            )

        # Prevent operations on inactive wallets.
        if wallet.status != WalletStatus.ACTIVE:
            raise ValueError("Wallet is not active")

        return wallet

    @staticmethod
    def get_user_wallets(
        db: Session,
        current_user: User,
    ) -> list[Wallet]:
        # Return all wallets belonging to the current user.
        return WalletRepository.get_all_by_user_id(
            db=db,
            user_id=current_user.id,
        )

    @staticmethod
    def update_wallet(
        db: Session,
        wallet_id: int,
        current_user: User,
        wallet_data: WalletUpdate,
    ) -> Wallet:
        wallet = WalletRepository.get_by_id(
            db=db,
            wallet_id=wallet_id,
        )

        if wallet is None:
            raise ValueError("Wallet not found")

        # Verify wallet ownership for customers.
        if (
            current_user.role == "CUSTOMER"
            and wallet.user_id != current_user.id
        ):
            raise PermissionError(
                "You are not authorized to update this wallet"
            )

        # Only active wallets can be updated.
        if wallet.status != WalletStatus.ACTIVE:
            raise ValueError(
                "Only active wallets can be updated"
            )

        update_data = wallet_data.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            raise ValueError(
                "At least one field is required to update"
            )

        # Update only fields permitted by WalletUpdate schema.
        for field, value in update_data.items():
            if value is not None:
                setattr(wallet, field, value)

        db.commit()
        db.refresh(wallet)

        return wallet
    
    
    @staticmethod
    def freeze_wallet(
       db: Session,
       wallet_id: int,
         current_user: User,
    ) -> Wallet:
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
            "You are not authorized to freeze this wallet"
        )

        if wallet.status != WalletStatus.ACTIVE:
          raise ValueError(
            f"Cannot freeze wallet with status {wallet.status}"
        )

        wallet.status = WalletStatus.FROZEN

        NotificationService.create_notification(
          db=db,
          user_id=wallet.user_id,
          notification_type=NotificationType.WALLET_FROZEN,
          title="Wallet Frozen",
           message=(
            f"Your wallet ID {wallet.id} has been frozen successfully."
        ),
    )

        db.commit()
        db.refresh(wallet)

        return wallet

    @staticmethod
    def unfreeze_wallet(
       db: Session,
       wallet_id: int,
       current_user: User,
    ) -> Wallet:
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
            "You are not authorized to unfreeze this wallet"
        )

        if wallet.status != WalletStatus.FROZEN:
           raise ValueError(
            f"Cannot unfreeze wallet with status {wallet.status}"
        )

        wallet.status = WalletStatus.ACTIVE

        NotificationService.create_notification(
          db=db,
          user_id=wallet.user_id,
          notification_type=NotificationType.WALLET_UNFROZEN,
          title="Wallet Unfrozen",
          message=(
            f"Your wallet ID {wallet.id} has been unfrozen successfully."
        ),
    )

        db.commit()
        db.refresh(wallet)

        return wallet