"""Moderation repository - MongoDB."""
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ModerationRepository:
    """Moderation repository."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.reports: AsyncIOMotorCollection = db["post_reports"]
        self.posts: AsyncIOMotorCollection = db["posts"]

    async def init_indexes(self) -> None:
        """Initialize indexes."""
        await self.reports.create_index("post_id")
        await self.reports.create_index("reporter_id")
        await self.reports.create_index("status")
        await self.reports.create_index([("post_id", 1), ("reporter_id", 1)], unique=True)
        logger.info("Moderation indexes created")

    async def report_post(self, report_data: Dict[str, Any]) -> str:
        """Report post."""
        report_data["created_at"] = datetime.now(timezone.utc)
        report_data["updated_at"] = datetime.now(timezone.utc)
        report_data["status"] = "pending"

        result = await self.reports.insert_one(report_data)
        return str(result.inserted_id)

    async def get_reports_for_post(self, post_id: str) -> List[Dict]:
        """Get all reports for a post."""
        reports = await self.reports.find({
            "post_id": post_id,
            "status": "pending",
        }).to_list(length=None)
        return reports

    async def get_pending_posts_count(self) -> int:
        """Get count of pending posts."""
        return await self.posts.count_documents({"status": "pending", "is_deleted": False})

    async def get_pending_posts(self, skip: int = 0, limit: int = 20) -> tuple[List[Dict], int]:
        """Get pending posts for moderation."""
        query = {"status": "pending", "is_deleted": False}
        total = await self.posts.count_documents(query)

        posts = await self.posts.find(query).sort("created_at", 1).skip(skip).limit(limit).to_list(length=None)

        # Add reports count for each post
        for post in posts:
            post_id = str(post["_id"])
            reports = await self.get_reports_for_post(post_id)
            post["reports_count"] = len(reports)

        return posts, total

    async def approve_post(self, post_id: str) -> bool:
        """Approve post."""
        try:
            result = await self.posts.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$set": {
                        "status": "published",
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error approving post {post_id}: {str(e)}")
            return False

    async def reject_post(self, post_id: str, rejection_reason: str) -> bool:
        """Reject post."""
        try:
            result = await self.posts.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$set": {
                        "status": "rejected",
                        "rejection_reason": rejection_reason,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error rejecting post {post_id}: {str(e)}")
            return False

    async def delete_post_by_moderation(self, post_id: str, reason: str) -> bool:
        """Delete post (soft delete) for violation."""
        try:
            result = await self.posts.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$set": {
                        "is_deleted": True,
                        "moderation_reason": reason,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deleting post {post_id}: {str(e)}")
            return False

    async def mark_report_resolved(self, report_id: str, action: str) -> bool:
        """Mark report as resolved."""
        try:
            result = await self.reports.update_one(
                {"_id": ObjectId(report_id)},
                {
                    "$set": {
                        "status": "resolved",
                        "action": action,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error marking report resolved {report_id}: {str(e)}")
            return False

    async def get_pending_reports_count(self) -> int:
        """Get count of pending reports."""
        return await self.reports.count_documents({"status": "pending"})

    async def get_statistics(self) -> Dict[str, int]:
        """Get moderation statistics."""
        pending_posts = await self.posts.count_documents({"status": "pending", "is_deleted": False})
        approved_posts = await self.posts.count_documents({"status": "published", "is_deleted": False})
        rejected_posts = await self.posts.count_documents({"status": "rejected", "is_deleted": False})
        pending_reports = await self.reports.count_documents({"status": "pending"})
        total_reports = await self.reports.count_documents({})

        return {
            "pending_posts": pending_posts,
            "pending_reports": pending_reports,
            "approved_posts": approved_posts,
            "rejected_posts": rejected_posts,
            "total_reports": total_reports,
        }
