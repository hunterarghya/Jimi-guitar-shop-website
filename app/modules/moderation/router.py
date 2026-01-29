"""Moderation router - API endpoints."""
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core import get_mongo_db
from app.core.security import get_current_user
from app.modules.moderation.service import ModerationService
from app.modules.moderation.schemas import (
    PostReportRequest,
    ModeratePostRequest,
    ModerationStatisticsResponse,
)
from app.middleware import AppException
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/moderation", tags=["moderation"])


@router.post("/posts/{post_id}/report", response_model=dict)
async def report_post(
    post_id: str,
    req: PostReportRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Report post."""
    service = ModerationService(db)
    return await service.report_post(post_id, current_user["sub"], req)


@router.put("/posts/{post_id}/approve", response_model=dict)
async def approve_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Approve post (admin only)."""
    if not current_user.get("is_admin"):
        raise AppException("Only admins can approve posts", 403)

    service = ModerationService(db)
    return await service.moderate_post(post_id, ModeratePostRequest(action="approve"))


@router.put("/posts/{post_id}/reject", response_model=dict)
async def reject_post(
    post_id: str,
    req: ModeratePostRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Reject post (admin only)."""
    if not current_user.get("is_admin"):
        raise AppException("Only admins can reject posts", 403)

    if req.action != "reject":
        raise AppException("Invalid action", 400)

    service = ModerationService(db)
    return await service.moderate_post(post_id, req)


@router.delete("/posts/{post_id}", response_model=dict)
async def delete_post_violation(
    post_id: str,
    reason: str = Query(..., min_length=5, max_length=500),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Delete post for violation (admin only)."""
    if not current_user.get("is_admin"):
        raise AppException("Only admins can delete posts", 403)

    service = ModerationService(db)
    return await service.delete_post(post_id, reason)


@router.get("/pending", response_model=dict)
async def get_pending_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get pending posts for moderation (admin only)."""
    if not current_user.get("is_admin"):
        raise AppException("Only admins can access moderation queue", 403)

    service = ModerationService(db)
    return await service.get_pending_posts(page=page, page_size=page_size)


@router.get("/statistics", response_model=ModerationStatisticsResponse)
async def get_statistics(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get moderation statistics (admin only)."""
    if not current_user.get("is_admin"):
        raise AppException("Only admins can view statistics", 403)

    service = ModerationService(db)
    return await service.get_statistics()
