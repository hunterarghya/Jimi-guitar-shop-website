"""Social repository - MongoDB data access."""
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class PostRepository:
    """Post repository."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.posts: AsyncIOMotorCollection = db["posts"]
        self.comments: AsyncIOMotorCollection = db["comments"]
        self.likes: AsyncIOMotorCollection = db["likes"]
        self.saves: AsyncIOMotorCollection = db["saves"]

    async def init_indexes(self) -> None:
        """Initialize MongoDB indexes."""
        # Posts
        await self.posts.create_index("user_id")
        await self.posts.create_index("status")
        await self.posts.create_index("created_at")
        await self.posts.create_index([("caption", "text"), ("tags", "text")])

        # Comments
        await self.comments.create_index("post_id")
        await self.comments.create_index("user_id")
        await self.comments.create_index("created_at")

        # Likes
        await self.likes.create_index("post_id")
        await self.likes.create_index("user_id")
        await self.likes.create_index([("post_id", 1), ("user_id", 1)], unique=True)

        # Saves
        await self.saves.create_index("post_id")
        await self.saves.create_index("user_id")
        await self.saves.create_index([("post_id", 1), ("user_id", 1)], unique=True)

        logger.info("Social indexes created")

    async def create_post(self, post_data: Dict[str, Any]) -> str:
        """Create post."""
        post_data["created_at"] = datetime.now(timezone.utc)
        post_data["updated_at"] = datetime.now(timezone.utc)
        post_data["status"] = "pending"  # Requires admin approval
        post_data["likes_count"] = 0
        post_data["comments_count"] = 0
        post_data["saves_count"] = 0
        post_data["is_deleted"] = False

        result = await self.posts.insert_one(post_data)
        return str(result.inserted_id)

    async def get_post(self, post_id: str, user_id: Optional[str] = None) -> Optional[Dict]:
        """Get post by ID."""
        try:
            doc = await self.posts.find_one({
                "_id": ObjectId(post_id),
                "is_deleted": False,
            })

            if not doc:
                return None

            # Add user interaction flags
            if user_id:
                like = await self.likes.find_one({"post_id": post_id, "user_id": user_id})
                doc["is_liked_by_user"] = like is not None

                save = await self.saves.find_one({"post_id": post_id, "user_id": user_id})
                doc["is_saved_by_user"] = save is not None

            return doc
        except Exception as e:
            logger.error(f"Error fetching post {post_id}: {str(e)}")
            return None

    async def update_post(self, post_id: str, update_data: Dict[str, Any]) -> bool:
        """Update post."""
        try:
            update_data["updated_at"] = datetime.now(timezone.utc)

            result = await self.posts.update_one(
                {
                    "_id": ObjectId(post_id),
                    "is_deleted": False,
                },
                {"$set": update_data},
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating post {post_id}: {str(e)}")
            return False

    async def soft_delete_post(self, post_id: str) -> bool:
        """Soft delete post."""
        try:
            result = await self.posts.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$set": {
                        "is_deleted": True,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deleting post {post_id}: {str(e)}")
            return False

    async def list_feed(
        self,
        status: str = "published",
        skip: int = 0,
        limit: int = 20,
        user_id: Optional[str] = None,
    ) -> tuple[List[Dict], int]:
        """List posts for feed."""
        query = {"is_deleted": False, "status": status}

        total = await self.posts.count_documents(query)

        posts = await self.posts.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)

        # Add user interaction flags
        if user_id:
            for post in posts:
                like = await self.likes.find_one({
                    "post_id": str(post["_id"]),
                    "user_id": user_id,
                })
                post["is_liked_by_user"] = like is not None

                save = await self.saves.find_one({
                    "post_id": str(post["_id"]),
                    "user_id": user_id,
                })
                post["is_saved_by_user"] = save is not None

        return posts, total

    async def list_user_posts(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        current_user_id: Optional[str] = None,
    ) -> tuple[List[Dict], int]:
        """List user's posts."""
        query = {"user_id": user_id, "is_deleted": False, "status": "published"}

        total = await self.posts.count_documents(query)

        posts = await self.posts.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)

        # Add user interaction flags
        if current_user_id and current_user_id != user_id:
            for post in posts:
                like = await self.likes.find_one({
                    "post_id": str(post["_id"]),
                    "user_id": current_user_id,
                })
                post["is_liked_by_user"] = like is not None

                save = await self.saves.find_one({
                    "post_id": str(post["_id"]),
                    "user_id": current_user_id,
                })
                post["is_saved_by_user"] = save is not None

        return posts, total

    # Comments
    async def add_comment(self, comment_data: Dict[str, Any]) -> str:
        """Add comment to post."""
        comment_data["created_at"] = datetime.now(timezone.utc)
        comment_data["updated_at"] = datetime.now(timezone.utc)
        comment_data["likes_count"] = 0
        comment_data["is_deleted"] = False

        result = await self.comments.insert_one(comment_data)

        # Increment post comment count
        await self.posts.update_one(
            {"_id": ObjectId(comment_data["post_id"])},
            {"$inc": {"comments_count": 1}},
        )

        return str(result.inserted_id)

    async def get_comments(
        self,
        post_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[Dict], int]:
        """Get comments for post."""
        query = {"post_id": post_id, "is_deleted": False}

        total = await self.comments.count_documents(query)

        comments = await self.comments.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)

        return comments, total

    async def delete_comment(self, comment_id: str, post_id: str) -> bool:
        """Delete comment."""
        try:
            result = await self.comments.update_one(
                {"_id": ObjectId(comment_id)},
                {
                    "$set": {
                        "is_deleted": True,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

            if result.modified_count > 0:
                # Decrement post comment count
                await self.posts.update_one(
                    {"_id": ObjectId(post_id)},
                    {"$inc": {"comments_count": -1}},
                )

            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deleting comment {comment_id}: {str(e)}")
            return False

    # Likes
    async def like_post(self, post_id: str, user_id: str, author_name: str) -> bool:
        """Like post."""
        try:
            await self.likes.insert_one({
                "post_id": post_id,
                "user_id": user_id,
                "author_name": author_name,
                "created_at": datetime.now(timezone.utc),
            })

            # Increment post likes count
            await self.posts.update_one(
                {"_id": ObjectId(post_id)},
                {"$inc": {"likes_count": 1}},
            )

            return True
        except Exception as e:
            logger.debug(f"Like already exists or error: {str(e)}")
            return False

    async def unlike_post(self, post_id: str, user_id: str) -> bool:
        """Unlike post."""
        try:
            result = await self.likes.delete_one({
                "post_id": post_id,
                "user_id": user_id,
            })

            if result.deleted_count > 0:
                # Decrement post likes count
                await self.posts.update_one(
                    {"_id": ObjectId(post_id)},
                    {"$inc": {"likes_count": -1}},
                )

            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error unliking post {post_id}: {str(e)}")
            return False

    async def get_likes(
        self,
        post_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[Dict], int]:
        """Get likes for post."""
        query = {"post_id": post_id}

        total = await self.likes.count_documents(query)

        likes = await self.likes.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)

        return likes, total

    # Saves
    async def save_post(self, post_id: str, user_id: str) -> bool:
        """Save post."""
        try:
            await self.saves.insert_one({
                "post_id": post_id,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
            })

            # Increment post saves count
            await self.posts.update_one(
                {"_id": ObjectId(post_id)},
                {"$inc": {"saves_count": 1}},
            )

            return True
        except Exception as e:
            logger.debug(f"Save already exists or error: {str(e)}")
            return False

    async def unsave_post(self, post_id: str, user_id: str) -> bool:
        """Unsave post."""
        try:
            result = await self.saves.delete_one({
                "post_id": post_id,
                "user_id": user_id,
            })

            if result.deleted_count > 0:
                # Decrement post saves count
                await self.posts.update_one(
                    {"_id": ObjectId(post_id)},
                    {"$inc": {"saves_count": -1}},
                )

            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error unsaving post {post_id}: {str(e)}")
            return False

    async def get_saved_posts(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Dict], int]:
        """Get saved posts for user."""
        # Get all saves for user
        saves = await self.saves.find({"user_id": user_id}).to_list(length=None)
        post_ids = [save["post_id"] for save in saves]

        # Get posts
        query = {
            "_id": {"$in": [ObjectId(pid) for pid in post_ids]},
            "is_deleted": False,
        }

        total = len(post_ids)

        posts = await self.posts.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)

        return posts, total
