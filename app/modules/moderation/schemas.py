"""Moderation schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ReportReason(str, Enum):
    """Report reasons."""
    SPAM = "spam"
    INAPPROPRIATE = "inappropriate"
    HATE_SPEECH = "hate_speech"
    MISINFORMATION = "misinformation"
    HARASSMENT = "harassment"
    OTHER = "other"


class PostReportRequest(BaseModel):
    """Report post request."""
    reason: ReportReason
    description: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "inappropriate",
                "description": "This post contains offensive content",
            }
        }


class ModeratePostRequest(BaseModel):
    """Moderate post request."""
    action: str = Field(..., pattern="^(approve|reject)$")
    rejection_reason: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "action": "reject",
                "rejection_reason": "Contains inappropriate content",
            }
        }


class PostReportResponse(BaseModel):
    """Post report response."""
    id: str = Field(alias="_id")
    post_id: str
    reporter_id: str
    reason: str
    description: Optional[str] = None
    status: str = "pending"
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class ModerationQueueResponse(BaseModel):
    """Moderation queue response."""
    id: str = Field(alias="_id")
    post_id: str
    user_id: str
    author_name: str
    caption: str
    images: List = []
    tags: List = []
    reports_count: int = 0
    created_at: datetime

    class Config:
        populate_by_name = True


class ModerationStatisticsResponse(BaseModel):
    """Moderation statistics."""
    pending_posts: int
    pending_reports: int
    approved_posts: int
    rejected_posts: int
    total_reports: int
