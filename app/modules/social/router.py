"""Social router - API endpoints."""
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_mongo_db, get_db
from app.core.security import get_current_user
from app.modules.social.service import SocialService
from app.modules.social.schemas import (
    PostResponse,
    PostListResponse,
    CreatePostRequest,
    UpdatePostRequest,
    CommentCreate,
    CommentResponse,
)
from app.middleware import AppException
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/posts", tags=["social"])


@router.get("", response_model=PostListResponse)
async def get_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get public feed."""
    user_id = current_user["sub"] if current_user else None
    service = SocialService(db)
    return await service.get_feed(user_id=user_id, page=page, page_size=page_size)


@router.post("", response_model=PostResponse)
async def create_post(
    req: CreatePostRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    pg_db: AsyncSession = Depends(get_db),
):
    """Create post (requires admin approval)."""
    from app.modules.users.service import UserService
    from uuid import UUID

    user_service = UserService(pg_db)
    user = await user_service.get_user_by_id(UUID(current_user["sub"]))

    service = SocialService(db)
    return await service.create_post(
        user_id=current_user["sub"],
        author_name=f"{user.first_name} {user.last_name}",
        req=req,
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get post by ID."""
    user_id = current_user["sub"] if current_user else None
    service = SocialService(db)
    return await service.get_post(post_id, user_id=user_id)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    req: UpdatePostRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Update post (owner only)."""
    service = SocialService(db)
    return await service.update_post(post_id, current_user["sub"], req)


@router.delete("/{post_id}", response_model=dict)
async def delete_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Delete post (owner only)."""
    service = SocialService(db)
    return await service.delete_post(post_id, current_user["sub"])


@router.get("/{post_id}/comments", response_model=dict)
async def get_comments(
    post_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get comments for post."""
    service = SocialService(db)
    return await service.get_comments(post_id, page=page, page_size=page_size)


@router.post("/{post_id}/comments", response_model=CommentResponse)
async def add_comment(
    post_id: str,
    req: CommentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    pg_db: AsyncSession = Depends(get_db),
):
    """Add comment to post."""
    # Get user name
    from app.modules.users.service import UserService
    from uuid import UUID

    try:
        user_service = UserService(pg_db)
        user = await user_service.get_user_by_id(UUID(current_user["sub"]))
        author_name = f"{user.first_name} {user.last_name}"
    except Exception as e:
        logger.warning(f"Could not fetch user details for comment: {str(e)}")
        author_name = "Anonymous"

    service = SocialService(db)
    return await service.add_comment(
        post_id=post_id,
        user_id=current_user["sub"],
        author_name=author_name,
        req=req,
    )


@router.delete("/{post_id}/comments/{comment_id}", response_model=dict)
async def delete_comment(
    post_id: str,
    comment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Delete comment (owner only)."""
    service = SocialService(db)
    return await service.delete_comment(comment_id, post_id, current_user["sub"])


@router.get("/{post_id}/likes", response_model=dict)
async def get_likes(
    post_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get likes for post."""
    service = SocialService(db)
    return await service.get_likes(post_id, page=page, page_size=page_size)


@router.post("/{post_id}/like", response_model=dict)
async def like_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    pg_db: AsyncSession = Depends(get_db),
):
    """Like post."""
    from app.modules.users.service import UserService
    from uuid import UUID

    try:
        user_service = UserService(pg_db)
        user = await user_service.get_user_by_id(UUID(current_user["sub"]))
        author_name = f"{user.first_name} {user.last_name}"
    except Exception as e:
        logger.warning(f"Could not fetch user details for like: {str(e)}")
        author_name = "Anonymous"

    service = SocialService(db)
    return await service.like_post(
        post_id=post_id,
        user_id=current_user["sub"],
        author_name=author_name,
    )


@router.delete("/{post_id}/like", response_model=dict)
async def unlike_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Unlike post."""
    service = SocialService(db)
    return await service.unlike_post(post_id, current_user["sub"])


@router.post("/{post_id}/save", response_model=dict)
async def save_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Save post."""
    service = SocialService(db)
    return await service.save_post(post_id, current_user["sub"])


@router.delete("/{post_id}/save", response_model=dict)
async def unsave_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Unsave post."""
    service = SocialService(db)
    return await service.unsave_post(post_id, current_user["sub"])


@router.get("/users/{user_id}/posts", response_model=PostListResponse)
async def get_user_posts(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get user's posts."""
    current_user_id = current_user["sub"] if current_user else None
    service = SocialService(db)
    return await service.get_user_posts(
        user_id=user_id,
        current_user_id=current_user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/users/{user_id}/saved", response_model=PostListResponse)
async def get_user_saved_posts(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get user's saved posts (owner only)."""
    if current_user["sub"] != user_id:
        raise AppException("Unauthorized", 403)

    service = SocialService(db)
    return await service.get_saved_posts(user_id=user_id, page=page, page_size=page_size)
