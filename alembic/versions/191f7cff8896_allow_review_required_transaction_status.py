"""allow review required transaction status"""

from typing import Sequence, Union

from alembic import op

revision: str = "191f7cff8896"
down_revision: Union[str, Sequence[str], None] = "8808e87ddf16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
 op.drop_constraint(
"check_transaction_status",
"transactions",
type_="check",
)


 op.create_check_constraint(
    "check_transaction_status",
    "transactions",
    """
    status IN (
        'PENDING',
        'PROCESSING',
        'REVIEW_REQUIRED',
        'COMPLETED',
        'FAILED',
        'CANCELLED'
    )
    """,
)


def downgrade() -> None:
# Do not remove the new status constraint while rows may use REVIEW_REQUIRED.
# A safe downgrade requires resolving all REVIEW_REQUIRED transactions first.
 op.drop_constraint(
"check_transaction_status",
"transactions",
type_="check",
)


 op.create_check_constraint(
    "check_transaction_status",
    "transactions",
    """
    status IN (
        'PENDING',
        'PROCESSING',
        'COMPLETED',
        'FAILED',
        'CANCELLED'
    )
    """,
)

