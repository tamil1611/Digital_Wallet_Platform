
"""add suspicious transaction alerts

Revision ID: 30d75567a1c9
Revises: f5eb41ea3fc2
Create Date: 2026-10-26 14:23:20.948308

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "30d75567a1c9"
down_revision: Union[str, Sequence[str], None] = "f5eb41ea3fc2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "suspicious_transaction_alerts",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "transaction_id",
            sa.Integer(),
            sa.ForeignKey("transactions.id"),
            nullable=False,
        ),
        sa.Column(
            "wallet_id",
            sa.Integer(),
            sa.ForeignKey("wallets.id"),
            nullable=False,
        ),
        sa.Column(
            "amount",
            sa.Numeric(18, 2),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="REVIEW_REQUIRED",
        ),
        sa.Column(
            "risk_reason",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "reviewed_by",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "review_notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_suspicious_transaction_alerts_transaction_id",
        "suspicious_transaction_alerts",
        ["transaction_id"],
    )

    op.create_index(
        "ix_suspicious_transaction_alerts_wallet_id",
        "suspicious_transaction_alerts",
        ["wallet_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_suspicious_transaction_alerts_wallet_id",
        table_name="suspicious_transaction_alerts",
    )

    op.drop_index(
        "ix_suspicious_transaction_alerts_transaction_id",
        table_name="suspicious_transaction_alerts",
    )

    op.drop_table("suspicious_transaction_alerts")

