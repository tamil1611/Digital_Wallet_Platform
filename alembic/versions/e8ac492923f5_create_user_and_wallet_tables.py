
"""Add role column to users

Revision ID: 2a96324336f6
Revises: 5ad5438a7c17
"""

from alembic import op
import sqlalchemy as sa


revision = "e8ac492923f5"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=30),
            server_default="CUSTOMER",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "role")

