"""create transaction limits table

Revision ID: 142ee4bc6c56
Revises: 6a17f5232c4d
Create Date: 2026-10-25 14:27:10.283599

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '142ee4bc6c56'
down_revision: Union[str, Sequence[str], None] = '6a17f5232c4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "transaction_limits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "max_transaction_amount",
            sa.Numeric(precision=15, scale=2),
            nullable=False,
        ),
        sa.Column(
            "daily_transfer_limit",
            sa.Numeric(precision=15, scale=2),
            nullable=False,
        ),
        sa.Column(
            "daily_withdrawal_limit",
            sa.Numeric(precision=15, scale=2),
            nullable=False,
        ),
        sa.Column(
            "max_transactions_per_day",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_transaction_limits_id"),
        "transaction_limits",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_transaction_limits_id"),
        table_name="transaction_limits",
    )

    op.drop_table("transaction_limits")

