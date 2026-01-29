"""Social media schemas for MongoDB."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PostImage(BaseModel):
    """Post image/media."""
    url: str
    media_type: str = "image"  # image, video, link


class CreatePostRequest(BaseModel):
    """Create post request."""
    caption: str = Field(..., min_length=1, max_length=5000)
    images: Optional[List[PostImage]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "caption": "Just picked up this beautiful acoustic guitar! 🎸",
                "images": [
                    {
                        "url": "https://imagekit.io/...",
                        "media_type": "image",
                    }
                ],
                "tags": ["guitar", "acoustic", "newgear"],
            }
        }


class UpdatePostRequest(BaseModel):
    """Update post request."""
    caption: Optional[str] = None
    images: Optional[List[PostImage]] = None
    tags: Optional[List[str]] = None


class CommentCreate(BaseModel):
    """Create comment request."""
    text: str = Field(..., min_length=1, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "text": "This is awesome! How much did it cost?",
            }
        }


class CommentResponse(BaseModel):
    """Comment response."""
    id: str = Field(alias="_id")
    post_id: str
    user_id: str
    author_name: str
    text: str
    likes_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class PostResponse(BaseModel):
    """Post response."""
    id: str = Field(alias="_id")
    user_id: str
    author_name: str
    caption: str
    images: List[PostImage] = []
    tags: List[str] = []
    likes_count: int = 0
    comments_count: int = 0
    saves_count: int = 0
    is_liked_by_user: bool = False
    is_saved_by_user: bool = False
    status: str = "published"
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class PostListResponse(BaseModel):
    """Post list response with pagination."""
    items: List[PostResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LikeResponse(BaseModel):
    """Like response."""
    id: str = Field(alias="_id")
    post_id: str
    user_id: str
    author_name: str
    created_at: datetime

    class Config:
        populate_by_name = True


class SaveResponse(BaseModel):
    """Save/bookmark response."""
    id: str = Field(alias="_id")
    post_id: str
    user_id: str
    created_at: datetime

    class Config:
        populate_by_name = True


class UserProfileResponse(BaseModel):
    """User profile for social."""
    user_id: str
    name: str
    email: str
    posts_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    is_followed_by_user: bool = False
    created_at: datetime
