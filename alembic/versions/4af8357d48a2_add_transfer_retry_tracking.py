"""add transfer retry tracking

Revision ID: 4af8357d48a2
Revises: 81d1a88f8347
Create Date: 2026-10-27 00:43:38.005580

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4af8357d48a2'
down_revision: Union[str, Sequence[str], None] = '81d1a88f8347'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.add_column(
        "transfers",
        sa.Column(
            "retry_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "transfers",
        sa.Column(
            "last_retry_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )




def downgrade() -> None:
    op.drop_column("transfers", "last_retry_at")
    op.drop_column("transfers", "retry_count")

