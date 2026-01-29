"""Alembic initialization script."""
from alembic.config import Config

alembic_cfg = Config("alembic.ini")
alembic_cfg.set_main_option(
    "sqlalchemy.url",
    "postgresql+asyncpg://postgres:postgres@localhost/jimi",
)
