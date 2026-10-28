"""Update wallet balance columns.

Revision ID: ab8c4a7bac7f
Revises: 7cb3c2852ce5
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ab8c4a7bac7f"
down_revision: Union[str, Sequence[str], None] = "7cb3c2852ce5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add available_balance and copy existing balances.
    op.add_column(
        "wallets",
        sa.Column(
            "available_balance",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
    )

    # 2. Add pending_balance.
    op.add_column(
        "wallets",
        sa.Column(
            "pending_balance",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
    )

    # 3. Preserve the existing wallet balances.
    op.execute(
        "UPDATE wallets "
        "SET available_balance = balance, pending_balance = 0.00"
    )

    # 4. Remove temporary defaults.
    op.alter_column(
        "wallets",
        "available_balance",
        server_default=None,
    )

    op.alter_column(
        "wallets",
        "pending_balance",
        server_default=None,
    )

    # 5. Convert status VARCHAR to PostgreSQL ENUM.
    wallet_status = sa.Enum(
        "ACTIVE",
        "FROZEN",
        "SUSPENDED",
        "CLOSED",
        name="wallet_status",
    )

    wallet_status.create(op.get_bind(), checkfirst=True)

    op.alter_column(
        "wallets",
        "status",
        existing_type=sa.VARCHAR(length=20),
        type_=wallet_status,
        existing_nullable=False,
        postgresql_using="status::wallet_status",
    )

    # 6. Remove the unique index on user_id.
    op.drop_index(
        op.f("ix_wallets_user_id"),
        table_name="wallets",
    )

    op.create_index(
        op.f("ix_wallets_user_id"),
        "wallets",
        ["user_id"],
        unique=False,
    )

    # 7. Drop the old balance column after copying its values.
    op.drop_column("wallets", "balance")


def downgrade() -> None:
    # 1. Restore the old balance column.
    op.add_column(
        "wallets",
        sa.Column(
            "balance",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
    )

    # 2. Copy available balances back.
    op.execute(
        "UPDATE wallets SET balance = available_balance"
    )

    op.alter_column(
        "wallets",
        "balance",
        server_default=None,
    )

    # 3. Restore the original unique index.
    op.drop_index(
        op.f("ix_wallets_user_id"),
        table_name="wallets",
    )

    op.create_index(
        op.f("ix_wallets_user_id"),
        "wallets",
        ["user_id"],
        unique=True,
    )

    # 4. Convert ENUM back to VARCHAR.
    op.alter_column(
        "wallets",
        "status",
        existing_type=sa.Enum(
            "ACTIVE",
            "FROZEN",
            "SUSPENDED",
            "CLOSED",
            name="wallet_status",
        ),
        type_=sa.VARCHAR(length=20),
        existing_nullable=False,
        postgresql_using="status::text",
    )

    # 5. Remove the ENUM type and new columns.
    op.drop_column("wallets", "pending_balance")
    op.drop_column("wallets", "available_balance")

    op.execute("DROP TYPE IF EXISTS wallet_status")