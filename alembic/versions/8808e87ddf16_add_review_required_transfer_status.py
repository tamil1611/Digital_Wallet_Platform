"""add review required transfer status"""

from typing import Sequence, Union

from alembic import op

revision: str = "8808e87ddf16"
down_revision: Union[str, Sequence[str], None] = "30d75567a1c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
 op.execute(
"ALTER TYPE transfer_status ADD VALUE IF NOT EXISTS 'REVIEW_REQUIRED'"
)

def downgrade() -> None:
# PostgreSQL does not support removing an enum value directly.
# Keep REVIEW_REQUIRED in the enum during downgrade.
 pass
