"""Social service - business logic."""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
from bson import ObjectId
from app.modules.social.repository import PostRepository
from app.modules.social.schemas import (
    PostResponse,
    PostListResponse,
    CreatePostRequest,
    UpdatePostRequest,
    CommentResponse,
    CommentCreate,
    LikeResponse,
    SaveResponse,
)
from app.middleware import AppException
import logging

logger = logging.getLogger(__name__)


class SocialService:
    """Social media service."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.repository = PostRepository(db)

    async def create_post(
        self,
        user_id: str,
        author_name: str,
        req: CreatePostRequest,
    ) -> PostResponse:
        """Create post (requires admin approval)."""
        post_data = {
            "user_id": user_id,
            "author_name": author_name,
            "caption": req.caption,
            "images": [img.model_dump() if hasattr(img, 'model_dump') else img for img in req.images] if req.images else [],
            "tags": req.tags,
        }

        post_id = await self.repository.create_post(post_data)
        logger.info(f"Post created (pending approval): {post_id}")

        post = await self.repository.get_post(post_id, user_id)
        return self._format_post_response(post)

    async def get_post(self, post_id: str, user_id: Optional[str] = None) -> PostResponse:
        """Get post by ID."""
        post = await self.repository.get_post(post_id, user_id)
        if not post:
            raise AppException("Post not found", 404)

        # Check if post is published or user is owner
        if post["status"] != "published" and post["user_id"] != user_id:
            raise AppException("Post not found", 404)

        return self._format_post_response(post)

    async def update_post(
        self,
        post_id: str,
        user_id: str,
        req: UpdatePostRequest,
    ) -> PostResponse:
        """Update post (owner only)."""
        post = await self.repository.get_post(post_id, user_id)
        if not post:
            raise AppException("Post not found", 404)

        if post["user_id"] != user_id:
            raise AppException("Unauthorized", 403)

        update_data = {}
        if req.caption:
            update_data["caption"] = req.caption
        if req.images:
            update_data["images"] = [img.model_dump() if hasattr(img, 'model_dump') else img for img in req.images]
        if req.tags:
            update_data["tags"] = req.tags

        success = await self.repository.update_post(post_id, update_data)
        if not success:
            raise AppException("Failed to update post", 500)

        logger.info(f"Post updated: {post_id}")

        post = await self.repository.get_post(post_id, user_id)
        return self._format_post_response(post)

    async def delete_post(self, post_id: str, user_id: str) -> dict:
        """Delete post (owner only)."""
        post = await self.repository.get_post(post_id, user_id)
        if not post:
            raise AppException("Post not found", 404)

        if post["user_id"] != user_id:
            raise AppException("Unauthorized", 403)

        success = await self.repository.soft_delete_post(post_id)
        if not success:
            raise AppException("Failed to delete post", 500)

        logger.info(f"Post deleted: {post_id}")
        return {"message": "Post deleted successfully"}

    async def get_feed(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PostListResponse:
        """Get published feed."""
        skip = (page - 1) * page_size

        posts, total = await self.repository.list_feed(
            status="published",
            skip=skip,
            limit=page_size,
            user_id=user_id,
        )

        formatted_posts = [self._format_post_response(p) for p in posts]

        total_pages = (total + page_size - 1) // page_size

        return PostListResponse(
            items=formatted_posts,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_user_posts(
        self,
        user_id: str,
        current_user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PostListResponse:
        """Get user's posts."""
        skip = (page - 1) * page_size

        posts, total = await self.repository.list_user_posts(
            user_id=user_id,
            skip=skip,
            limit=page_size,
            current_user_id=current_user_id,
        )

        formatted_posts = [self._format_post_response(p) for p in posts]

        total_pages = (total + page_size - 1) // page_size

        return PostListResponse(
            items=formatted_posts,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def add_comment(
        self,
        post_id: str,
        user_id: str,
        author_name: str,
        req: CommentCreate,
    ) -> CommentResponse:
        """Add comment to post."""
        post = await self.repository.get_post(post_id)
        if not post:
            raise AppException("Post not found", 404)

        comment_data = {
            "post_id": post_id,
            "user_id": user_id,
            "author_name": author_name,
            "text": req.text,
        }

        comment_id = await self.repository.add_comment(comment_data)
        logger.info(f"Comment added: {comment_id}")

        comment = await self.repository.comments.find_one({"_id": ObjectId(comment_id)})
        return self._format_comment_response(comment)

    async def get_comments(
        self,
        post_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """Get comments for post."""
        post = await self.repository.get_post(post_id)
        if not post:
            raise AppException("Post not found", 404)

        skip = (page - 1) * page_size

        comments, total = await self.repository.get_comments(
            post_id=post_id,
            skip=skip,
            limit=page_size,
        )

        formatted_comments = [self._format_comment_response(c) for c in comments]

        total_pages = (total + page_size - 1) // page_size

        return {
            "items": formatted_comments,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def delete_comment(
        self,
        comment_id: str,
        post_id: str,
        user_id: str,
    ) -> dict:
        """Delete comment (owner only)."""
        from bson import ObjectId

        comment = await self.repository.comments.find_one({
            "_id": ObjectId(comment_id),
            "post_id": post_id,
        })

        if not comment:
            raise AppException("Comment not found", 404)

        if comment["user_id"] != user_id:
            raise AppException("Unauthorized", 403)

        success = await self.repository.delete_comment(comment_id, post_id)
        if not success:
            raise AppException("Failed to delete comment", 500)

        logger.info(f"Comment deleted: {comment_id}")
        return {"message": "Comment deleted successfully"}

    async def like_post(self, post_id: str, user_id: str, author_name: str) -> dict:
        """Like post."""
        post = await self.repository.get_post(post_id)
        if not post:
            raise AppException("Post not found", 404)

        success = await self.repository.like_post(post_id, user_id, author_name)
        if not success:
            raise AppException("Already liked this post", 400)

        logger.info(f"Post liked: {post_id} by {user_id}")
        return {"message": "Post liked"}

    async def unlike_post(self, post_id: str, user_id: str) -> dict:
        """Unlike post."""
        post = await self.repository.get_post(post_id)
        if not post:
            raise AppException("Post not found", 404)

        success = await self.repository.unlike_post(post_id, user_id)
        if not success:
            raise AppException("Post not liked", 400)

        logger.info(f"Post unliked: {post_id} by {user_id}")
        return {"message": "Post unliked"}

    async def get_likes(
        self,
        post_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """Get likes for post."""
        post = await self.repository.get_post(post_id)
        if not post:
            raise AppException("Post not found", 404)

        skip = (page - 1) * page_size

        likes, total = await self.repository.get_likes(
            post_id=post_id,
            skip=skip,
            limit=page_size,
        )

        formatted_likes = [self._format_like_response(l) for l in likes]

        total_pages = (total + page_size - 1) // page_size

        return {
            "items": formatted_likes,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def save_post(self, post_id: str, user_id: str) -> dict:
        """Save post."""
        post = await self.repository.get_post(post_id)
        if not post:
            raise AppException("Post not found", 404)

        success = await self.repository.save_post(post_id, user_id)
        if not success:
            raise AppException("Already saved this post", 400)

        logger.info(f"Post saved: {post_id} by {user_id}")
        return {"message": "Post saved"}

    async def unsave_post(self, post_id: str, user_id: str) -> dict:
        """Unsave post."""
        post = await self.repository.get_post(post_id)
        if not post:
            raise AppException("Post not found", 404)

        success = await self.repository.unsave_post(post_id, user_id)
        if not success:
            raise AppException("Post not saved", 400)

        logger.info(f"Post unsaved: {post_id} by {user_id}")
        return {"message": "Post unsaved"}

    async def get_saved_posts(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PostListResponse:
        """Get saved posts for user."""
        skip = (page - 1) * page_size

        posts, total = await self.repository.get_saved_posts(
            user_id=user_id,
            skip=skip,
            limit=page_size,
        )

        formatted_posts = [self._format_post_response(p) for p in posts]

        total_pages = (total + page_size - 1) // page_size

        return PostListResponse(
            items=formatted_posts,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def _format_post_response(self, post: dict) -> PostResponse:
        """Format MongoDB post to response."""
        from bson import ObjectId
        
        post_id = str(post["_id"]) if isinstance(post.get("_id"), ObjectId) else post.get("_id")
        
        return PostResponse(
            id=post_id,
            user_id=post.get("user_id"),
            author_name=post.get("author_name"),
            caption=post.get("caption"),
            images=post.get("images", []),
            tags=post.get("tags", []),
            likes_count=post.get("likes_count", 0),
            comments_count=post.get("comments_count", 0),
            saves_count=post.get("saves_count", 0),
            is_liked_by_user=post.get("is_liked_by_user", False),
            is_saved_by_user=post.get("is_saved_by_user", False),
            status=post.get("status", "published"),
            created_at=post.get("created_at"),
            updated_at=post.get("updated_at"),
        )

    def _format_comment_response(self, comment: dict) -> CommentResponse:
        """Format MongoDB comment to response."""
        from bson import ObjectId
        
        comment_id = str(comment["_id"]) if isinstance(comment.get("_id"), ObjectId) else comment.get("_id")
        
        return CommentResponse(
            id=comment_id,
            post_id=comment.get("post_id"),
            user_id=comment.get("user_id"),
            author_name=comment.get("author_name"),
            text=comment.get("text"),
            likes_count=comment.get("likes_count", 0),
            created_at=comment.get("created_at"),
            updated_at=comment.get("updated_at"),
        )

    def _format_like_response(self, like: dict) -> LikeResponse:
        """Format MongoDB like to response."""
        from bson import ObjectId
        
        like_id = str(like["_id"]) if isinstance(like.get("_id"), ObjectId) else like.get("_id")
        
        return LikeResponse(
            id=like_id,
            post_id=like.get("post_id"),
            user_id=like.get("user_id"),
            author_name=like.get("author_name"),
            created_at=like.get("created_at"),
        )
