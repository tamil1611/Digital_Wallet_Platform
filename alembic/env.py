from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.database import Base

# Import all models so Alembic can detect their tables.
from app.models.user import User  # noqa: F401
from app.models.wallet import Wallet  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.deposit import Deposit  # noqa: F401
from app.models.transfer import Transfer  # noqa: F401
from app.models.withdrawal import Withdrawal  # noqa: F401
from app.models.idempotency import IdempotencyRecord # noqa: F401
from app.models.transaction_limit import TransactionLimit  # noqa: F401
from app.models.refund import Refund, RefundStatus
from app.models.audit_log import AuditLog  # noqa: F401


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Read the database URL from .env through application settings.
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("%", "%%"),
)

# Register SQLAlchemy metadata for Alembic autogenerate.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
