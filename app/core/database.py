"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis
from app.core.config import get_settings
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

# PostgreSQL Engine & Session
_pg_engine = None
_async_session_factory = None

# MongoDB Client & Database
_mongo_client = None
_mongo_db = None

# Redis Client
_redis_client = None


async def init_pg(settings=None) -> None:
    """Initialize PostgreSQL async engine and session factory."""
    global _pg_engine, _async_session_factory
    
    if settings is None:
        settings = get_settings()
    
    _pg_engine = create_async_engine(
        settings.POSTGRES_URL,
        echo=settings.DEBUG,
        future=True,
        pool_size=20,
        max_overflow=40,
        pool_recycle=3600,
    )
    
    _async_session_factory = async_sessionmaker(
        _pg_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    logger.info("PostgreSQL engine initialized")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get PostgreSQL database session."""
    if _async_session_factory is None:
        await init_pg()
    
    async with _async_session_factory() as session:
        yield session


async def init_mongo(settings=None) -> None:
    """Initialize MongoDB connection."""
    global _mongo_client, _mongo_db
    
    if settings is None:
        settings = get_settings()
    
    _mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
    _mongo_db = _mongo_client[settings.MONGO_DB]
    
    # Test connection
    await _mongo_client.admin.command("ping")
    logger.info("MongoDB connected")


async def get_mongo_db() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance."""
    if _mongo_db is None:
        await init_mongo()
    return _mongo_db


async def init_redis(settings=None) -> None:
    """Initialize Redis connection."""
    global _redis_client
    
    if settings is None:
        settings = get_settings()
    
    _redis_client = await Redis.from_url(
        settings.REDIS_URL,
        encoding="utf8",
        decode_responses=True,
    )
    
    # Test connection
    await _redis_client.ping()
    logger.info("Redis connected")


async def get_redis() -> Redis:
    """Get Redis client instance."""
    if _redis_client is None:
        await init_redis()
    return _redis_client


async def close_connections() -> None:
    """Close all database connections."""
    global _pg_engine, _mongo_client, _redis_client
    
    if _pg_engine:
        await _pg_engine.dispose()
        logger.info("PostgreSQL engine disposed")
    
    if _mongo_client:
        _mongo_client.close()
        logger.info("MongoDB connection closed")
    
    if _redis_client:
        await _redis_client.close()
        logger.info("Redis connection closed")
