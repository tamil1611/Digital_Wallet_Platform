"""create withdrawals table

Revision ID: 6a17f5232c4d
Revises: 8538303e6d99
Create Date: 2026-10-21 16:43:13.850344
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6a17f5232c4d"
down_revision: Union[str, Sequence[str], None] = "8538303e6d99"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "withdrawals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "PROCESSING",
                "COMPLETED",
                "FAILED",
                "CANCELLED",
                name="withdrawal_status",
            ),
            nullable=False,
        ),
        sa.Column("reference_number", sa.String(length=100), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "amount > 0",
            name="check_withdrawal_amount_positive",
        ),
        sa.ForeignKeyConstraint(
            ["wallet_id"],
            ["wallets.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_withdrawals_id",
        "withdrawals",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_withdrawals_wallet_id",
        "withdrawals",
        ["wallet_id"],
        unique=False,
    )

    op.create_index(
        "ix_withdrawals_reference_number",
        "withdrawals",
        ["reference_number"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_withdrawals_reference_number", table_name="withdrawals")
    op.drop_index("ix_withdrawals_wallet_id", table_name="withdrawals")
    op.drop_index("ix_withdrawals_id", table_name="withdrawals")
    op.drop_table("withdrawals")

    sa.Enum(
        "PENDING",
        "PROCESSING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        name="withdrawal_status",
    ).drop(op.get_bind(), checkfirst=True)