"""Moderation service."""
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.modules.moderation.repository import ModerationRepository
from app.modules.moderation.schemas import (
    PostReportRequest,
    ModeratePostRequest,
    ModerationStatisticsResponse,
)
from app.middleware import AppException
import logging

logger = logging.getLogger(__name__)


class ModerationService:
    """Moderation service."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.repository = ModerationRepository(db)

    async def report_post(
        self,
        post_id: str,
        reporter_id: str,
        req: PostReportRequest,
    ) -> dict:
        """Report post."""
        # Check if already reported by this user
        from bson import ObjectId
        existing = await self.repository.reports.find_one({
            "post_id": post_id,
            "reporter_id": reporter_id,
        })

        if existing:
            raise AppException("You have already reported this post", 400)

        report_data = {
            "post_id": post_id,
            "reporter_id": reporter_id,
            "reason": req.reason.value,
            "description": req.description,
        }

        report_id = await self.repository.report_post(report_data)
        logger.info(f"Post reported: {post_id} by {reporter_id}")

        return {
            "message": "Post reported successfully",
            "report_id": report_id,
        }

    async def moderate_post(
        self,
        post_id: str,
        req: ModeratePostRequest,
    ) -> dict:
        """Moderate post (admin only)."""
        if req.action == "approve":
            success = await self.repository.approve_post(post_id)
            if not success:
                raise AppException("Post not found or already moderated", 404)

            logger.info(f"Post approved: {post_id}")
            return {"message": "Post approved"}

        elif req.action == "reject":
            if not req.rejection_reason:
                raise AppException("Rejection reason required", 400)

            success = await self.repository.reject_post(post_id, req.rejection_reason)
            if not success:
                raise AppException("Post not found or already moderated", 404)

            logger.info(f"Post rejected: {post_id}")
            return {"message": "Post rejected"}

        raise AppException("Invalid action", 400)

    async def delete_post(
        self,
        post_id: str,
        reason: str,
    ) -> dict:
        """Delete post (admin only)."""
        success = await self.repository.delete_post_by_moderation(post_id, reason)
        if not success:
            raise AppException("Post not found", 404)

        logger.info(f"Post deleted by moderation: {post_id}")
        return {"message": "Post deleted for violation"}

    async def get_pending_posts(self, page: int = 1, page_size: int = 20) -> dict:
        """Get pending posts for moderation."""
        skip = (page - 1) * page_size

        posts, total = await self.repository.get_pending_posts(skip=skip, limit=page_size)

        total_pages = (total + page_size - 1) // page_size

        return {
            "items": [self._format_post_for_moderation(p) for p in posts],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def get_statistics(self) -> ModerationStatisticsResponse:
        """Get moderation statistics."""
        stats = await self.repository.get_statistics()
        return ModerationStatisticsResponse(**stats)

    def _format_post_for_moderation(self, post: dict) -> dict:
        """Format post for moderation view."""
        from bson import ObjectId

        post_id = str(post["_id"]) if isinstance(post.get("_id"), ObjectId) else post.get("_id")

        return {
            "id": post_id,
            "post_id": post_id,
            "user_id": post.get("user_id"),
            "author_name": post.get("author_name"),
            "caption": post.get("caption"),
            "images": post.get("images", []),
            "tags": post.get("tags", []),
            "reports_count": post.get("reports_count", 0),
            "created_at": post.get("created_at"),
        }
