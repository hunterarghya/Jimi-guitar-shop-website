"""Alembic configuration and setup."""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.core.config import get_settings
from app.core.database import _pg_engine
import asyncio

# Get config from context
config = context.config

# Setup PostgreSQL URL
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.POSTGRES_URL)

# Interpret config for logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Build synchronous URL from async settings
    settings = get_settings()
    sync_url = settings.POSTGRES_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = sync_url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=None,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
