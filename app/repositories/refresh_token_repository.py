from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Save a hashed refresh token in the database."""
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
        )

        db.add(refresh_token)
        db.commit()
        db.refresh(refresh_token)

        return refresh_token

    @staticmethod
    def get_by_hash(
        db: Session,
        token_hash: str,
    ) -> RefreshToken | None:
        """Find a refresh token using its hash."""
        return (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )

    @staticmethod
    def revoke(
        db: Session,
        refresh_token: RefreshToken,
    ) -> RefreshToken:
        """Revoke a refresh token."""
        refresh_token.is_revoked = True
        db.commit()
        db.refresh(refresh_token)

        return refresh_token

    @staticmethod
    def revoke_all_for_user(
        db: Session,
        user_id: int,
    ) -> None:
        """Revoke all active refresh tokens belonging to a user."""
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked.is_(False),
        ).update(
            {RefreshToken.is_revoked: True},
            synchronize_session=False,
        )

        db.commit()