

"""create transfers table

Revision ID: 8687058cfddb
Revises: 323a0bb2cc77
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8687058cfddb"
down_revision: Union[str, Sequence[str], None] = "323a0bb2cc77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


transfer_status = sa.Enum(
    "PENDING",
    "PROCESSING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    name="transfer_status",
)


def upgrade() -> None:
    bind = op.get_bind()

    # Create the PostgreSQL ENUM type first.
    transfer_status.create(bind, checkfirst=True)

    op.create_table(
        "transfers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("sender_wallet_id", sa.Integer(), nullable=False),
        sa.Column("receiver_wallet_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column(
            "status",
            transfer_status,
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("reference", sa.String(100), nullable=False),
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
    op.drop_index(
        "ix_transfers_receiver_wallet_id",
        table_name="transfers",
    )
    op.drop_index(
        "ix_transfers_sender_wallet_id",
        table_name="transfers",
    )
    op.drop_index("ix_transfers_id", table_name="transfers")

    op.drop_table("transfers")

    transfer_status.drop(op.get_bind(), checkfirst=True)

