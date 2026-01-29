"""User schemas."""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email_verified: bool
    phone_verified: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """Update profile request."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+919876543210",
            }
        }
