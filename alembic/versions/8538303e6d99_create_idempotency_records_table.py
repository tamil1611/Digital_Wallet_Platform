"""create idempotency records table

Revision ID: 8538303e6d99
Revises: 4c50e57da0c5
Create Date: 2026-10-21 14:03:27.320718
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8538303e6d99"
down_revision: Union[str, Sequence[str], None] = "4c50e57da0c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create idempotency records table."""

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("operation", sa.String(length=50), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="PROCESSING",
        ),
        sa.Column("response_body", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_idempotency_user_key",
        ),
    )

    op.create_index(
        "ix_idempotency_records_id",
        "idempotency_records",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_idempotency_records_user_id",
        "idempotency_records",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop idempotency records table."""

    op.drop_index(
        "ix_idempotency_records_user_id",
        table_name="idempotency_records",
    )

    op.drop_index(
        "ix_idempotency_records_id",
        table_name="idempotency_records",
    )

    op.drop_table("idempotency_records")