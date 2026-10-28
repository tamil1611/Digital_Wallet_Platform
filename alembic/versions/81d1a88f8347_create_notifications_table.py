
"""create notifications table

Revision ID: 81d1a88f8347
Revises: b8c794932efc
Create Date: 2026-10-26 16:01:43.393005
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "81d1a88f8347"
down_revision: Union[str, Sequence[str], None] = "b8c794932efc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create notifications table."""

    notification_type = postgresql.ENUM(
        "DEPOSIT_COMPLETED",
        "DEPOSIT_FAILED",
        "TRANSFER_RECEIVED",
        "TRANSFER_COMPLETED",
        "TRANSFER_FAILED",
        "WITHDRAWAL_COMPLETED",
        "WITHDRAWAL_FAILED",
        "WALLET_FROZEN",
        "WALLET_UNFROZEN",
        "REFUND_APPROVED",
        "SUSPICIOUS_TRANSACTION_DETECTED",
        name="notification_type",
        
)
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "notification_type",
            notification_type,
            nullable=False,
        ),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "is_read",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_notifications_user_id",
        "notifications",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_notifications_is_read",
        "notifications",
        ["is_read"],
        unique=False,
    )


def downgrade() -> None:
    """Drop notifications table."""

    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    sa.Enum(
        name="notification_type"
    ).drop(op.get_bind(), checkfirst=True)

