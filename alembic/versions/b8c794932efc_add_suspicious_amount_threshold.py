"""add suspicious amount threshold"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c794932efc"
down_revision: Union[str, Sequence[str], None] = "191f7cff8896"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transaction_limits",
        sa.Column(
            "suspicious_amount_threshold",
            sa.Numeric(15, 2),
            nullable=False,
            server_default="10000.00",
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "transaction_limits",
        "suspicious_amount_threshold",
    )