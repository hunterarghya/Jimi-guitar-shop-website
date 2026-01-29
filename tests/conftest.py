"""Pytest configuration."""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.api import create_app
from app.core.database import get_db
from app.core.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_settings() -> Settings:
    """Get test settings."""
    return Settings(
        POSTGRES_HOST="localhost",
        POSTGRES_DB="jimi_test",
        DEBUG=True,
        TESTING=True,
    )


@pytest.fixture
async def db_session(test_settings) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    engine = create_async_engine(
        test_settings.POSTGRES_URL,
        echo=False,
    )
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(lambda: None)  # Create tables
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(lambda: None)  # Drop tables
    
    await engine.dispose()


@pytest.fixture
def app():
    """Create FastAPI test app."""
    return create_app()


@pytest.fixture
async def client(app):
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
