"""User router - API endpoints."""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core import get_db
from app.core.security import get_current_user
from app.middleware import AppException
from app.modules.users.service import UserService
from app.modules.users.schemas import UserProfileResponse, UpdateProfileRequest
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user profile."""
    service = UserService(db)
    return await service.get_profile(current_user["sub"])


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    req: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile."""
    service = UserService(db)
    return await service.update_profile(current_user["sub"], req.dict(exclude_unset=True))


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get user profile by ID."""
    try:
        uid = UUID(user_id)
    except ValueError:
        raise AppException("Invalid user ID", 400)

    service = UserService(db)
    return await service.get_profile(uid)
