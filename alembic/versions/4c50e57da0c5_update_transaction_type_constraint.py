"""update transaction type constraint"""

from alembic import op


# Revision identifiers
revision = "4c50e57da0c5"
down_revision = "8cef4cceda11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove the old transaction type constraint
    op.drop_constraint(
        "check_transaction_type",
        "transactions",
        type_="check",
    )

    # Add the updated constraint
    op.create_check_constraint(
        "check_transaction_type",
        "transactions",
        """
        transaction_type IN (
            'DEPOSIT',
            'WITHDRAWAL',
            'TRANSFER',
            'TRANSFER_DEBIT',
            'TRANSFER_CREDIT',
            'REFUND',
            'FEE',
            'ADJUSTMENT',
            'REVERSAL'
        )
        """,
    )


def downgrade() -> None:
    # Remove the updated constraint
    op.drop_constraint(
        "check_transaction_type",
        "transactions",
        type_="check",
    )

    # Restore the original constraint
    op.create_check_constraint(
        "check_transaction_type",
        "transactions",
        """
        transaction_type IN (
            'DEPOSIT',
            'WITHDRAWAL',
            'TRANSFER',
            'REFUND'
        )
        """,
    )