"""add immutable transaction ledger fields

Revision ID: d7d2abc7602d
Revises: 8687058cfddb
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7d2abc7602d"
down_revision: Union[str, Sequence[str], None] = "8687058cfddb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add ledger columns without breaking existing records.
    op.add_column(
        "transactions",
        sa.Column("balance_before", sa.Numeric(18, 2), nullable=True),
    )

    op.add_column(
        "transactions",
        sa.Column("balance_after", sa.Numeric(18, 2), nullable=True),
    )

    op.add_column(
        "transactions",
        sa.Column("reference_entity", sa.String(50), nullable=True),
    )

    op.add_column(
        "transactions",
        sa.Column("created_by", sa.Integer(), nullable=True),
    )

    op.add_column(
        "transactions",
        sa.Column("metadata", sa.JSON(), nullable=True),
    )

    # Allow multiple ledger records to share the same reference ID.
    op.drop_index(
        "ix_transactions_reference_id",
        table_name="transactions",
    )

    op.create_index(
        "ix_transactions_reference_id",
        "transactions",
        ["reference_id"],
        unique=False,
    )

    op.create_index(
        "ix_transactions_reference_entity",
        "transactions",
        ["reference_entity"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_transactions_created_by_users",
        "transactions",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Remove mutable timestamp from the ledger.
    op.drop_column("transactions", "updated_at")

    # Prevent normal SQL UPDATE and DELETE operations on ledger records.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_transaction_ledger_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION
                'Transaction ledger records cannot be updated or deleted';
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_prevent_transaction_ledger_mutation
        BEFORE UPDATE OR DELETE ON transactions
        FOR EACH ROW
        EXECUTE FUNCTION prevent_transaction_ledger_mutation();
        """
    )


def downgrade() -> None:
    # Remove trigger before attempting schema rollback.
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_prevent_transaction_ledger_mutation
        ON transactions;
        """
    )

    op.execute(
        """
        DROP FUNCTION IF EXISTS prevent_transaction_ledger_mutation();
        """
    )

    op.add_column(
        "transactions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.drop_constraint(
        "fk_transactions_created_by_users",
        "transactions",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_transactions_reference_entity",
        table_name="transactions",
    )

    op.drop_index(
        "ix_transactions_reference_id",
        table_name="transactions",
    )

    op.create_index(
        "ix_transactions_reference_id",
        "transactions",
        ["reference_id"],
        unique=True,
    )

    op.drop_column("transactions", "metadata")
    op.drop_column("transactions", "created_by")
    op.drop_column("transactions", "reference_entity")
    op.drop_column("transactions", "balance_after")
    op.drop_column("transactions", "balance_before")