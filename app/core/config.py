"""Configuration management using Pydantic Settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # Application
    APP_NAME: str = "Jimi - Guitar Shop Platform"
    APP_VERSION: str = "1.0.0"
    ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    TESTING: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # Database - PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "jimi"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "xxx"

    @property
    def POSTGRES_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Database - MongoDB
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_DB: str = "jimi"
    MONGO_USER: str = "mongodb"
    MONGO_PASSWORD: str = "xxx"

    @property
    def MONGO_URL(self) -> str:
        return f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = "xxx"

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # JWT
    SECRET_KEY: str = "xxx-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OAuth
    GOOGLE_CLIENT_ID: str = "xxx"
    GOOGLE_CLIENT_SECRET: str = "xxx"

    # Razorpay
    RAZORPAY_KEY_ID: str = "xxx"
    RAZORPAY_KEY_SECRET: str = "xxx"

    # ImageKit
    IMAGEKIT_PRIVATE_KEY: str = "xxx"
    IMAGEKIT_PUBLIC_KEY: str = "xxx"
    IMAGEKIT_URL_ENDPOINT: str = "xxx"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "xxx"
    SMTP_PASSWORD: str = "xxx"
    SENDER_EMAIL: str = "noreply@jimi.local"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Security
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    CSRF_ENABLED: bool = True

    # Geolocation
    SHOP_RADIUS_KM: float = 10.0
    SHOP_LATITUDE: float = 28.6139  # Delhi default
    SHOP_LONGITUDE: float = 77.2090

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
