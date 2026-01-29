"""User service - business logic."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.modules.users.models import User
from app.middleware import AppException
import logging

logger = logging.getLogger(__name__)


class UserService:
    """User service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: UUID) -> User:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if not user:
            raise AppException("User not found", 404)

        return user

    async def get_user_by_email(self, email: str) -> User:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if not user:
            raise AppException("User not found", 404)

        return user

    async def get_profile(self, user_id: UUID) -> dict:
        """Get user profile."""
        user = await self.get_user_by_id(user_id)

        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "email_verified": user.email_verified,
            "phone_verified": user.phone_verified,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

    async def update_profile(self, user_id: UUID, data: dict) -> dict:
        """Update user profile."""
        user = await self.get_user_by_id(user_id)

        # Update allowed fields
        for field in ["first_name", "last_name", "phone"]:
            if field in data:
                setattr(user, field, data[field])

        await self.db.commit()

        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "email_verified": user.email_verified,
            "phone_verified": user.phone_verified,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
