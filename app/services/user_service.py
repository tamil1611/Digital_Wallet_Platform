from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:

    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        email = str(user_data.email).lower()

        existing_user = UserRepository.get_by_email(db, email)

        if existing_user:
            raise ValueError("Email is already registered")

        hashed_password = get_password_hash(user_data.password)

        return UserRepository.create(
            db=db,
            user_data=user_data,
            hashed_password=hashed_password,
        )

    @staticmethod
    def login_user(
        db: Session,
        email: str,
        password: str,
    ) -> dict[str, str]:
        user = UserRepository.get_by_email(db, email.lower())

        if user is None or not verify_password(
            password,
            user.hashed_password,
        ):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("User account is inactive")

        access_token = create_access_token(
            subject=str(user.id)
        )

        refresh_token = create_refresh_token()
        token_hash = hash_refresh_token(refresh_token)

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        RefreshTokenRepository.create(
            db=db,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
        
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> dict[str, str]:
        token_hash = hash_refresh_token(refresh_token)

        stored_token = RefreshTokenRepository.get_by_hash(
            db,
            token_hash,
        )

        if stored_token is None:
            raise ValueError("Invalid refresh token")

        if stored_token.is_revoked:
            raise ValueError("Refresh token has been revoked")

        if stored_token.expires_at <= datetime.now(timezone.utc):
            raise ValueError("Refresh token has expired")

        user = UserRepository.get_by_id(db, stored_token.user_id)

        if user is None or not user.is_active:
            raise ValueError("User not found or inactive")

        access_token = create_access_token(subject=str(user.id))

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }
        
    @staticmethod
    def logout_user(db: Session, refresh_token: str) -> dict[str, str]:
        token_hash = hash_refresh_token(refresh_token)

        stored_token = RefreshTokenRepository.get_by_hash(
            db,
            token_hash,
        )

        if stored_token is None or stored_token.is_revoked:
            raise ValueError("Invalid refresh token")

        RefreshTokenRepository.revoke(db, stored_token)

        return {"message": "Logout successful"}

    @staticmethod
    def get_user_by_id(
        db: Session,
        user_id: int,
    ) -> User:
        user = UserRepository.get_by_id(db, user_id)

        if user is None:
            raise ValueError("User not found")

        return user
    
    @staticmethod
    def change_password(
        db: Session,
        user: User,
        current_password: str,
        new_password: str,
    ) -> dict[str, str]:
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")

        if verify_password(new_password, user.hashed_password):
            raise ValueError(
                "New password must be different from current password"
            )

        user.hashed_password = get_password_hash(new_password)
        db.commit()

        RefreshTokenRepository.revoke_all_for_user(db, user.id)

        return {"message": "Password changed successfully"}