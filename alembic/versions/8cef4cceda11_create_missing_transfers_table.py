
"""create missing transfers table

Revision ID: 8cef4cceda11
Revises: d7d2abc7602d
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8cef4cceda11"
down_revision: Union[str, Sequence[str], None] = "d7d2abc7602d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


transfer_status = sa.Enum(
    "PENDING",
    "PROCESSING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    name="transfer_status",
    create_type = False,
)


def upgrade() -> None:
    bind = op.get_bind()

    transfer_status.create(bind, checkfirst=True)

    op.create_table(
        "transfers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sender_wallet_id", sa.Integer(), nullable=False),
        sa.Column("receiver_wallet_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "status",
            transfer_status,
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("reference", sa.String(length=100), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["sender_wallet_id"],
            ["wallets.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["receiver_wallet_id"],
            ["wallets.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("reference"),
    )

    op.create_index(
        "ix_transfers_id",
        "transfers",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_transfers_sender_wallet_id",
        "transfers",
        ["sender_wallet_id"],
        unique=False,
    )

    op.create_index(
        "ix_transfers_receiver_wallet_id",
        "transfers",
        ["receiver_wallet_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("transfers")
    transfer_status.drop(op.get_bind(), checkfirst=True)

