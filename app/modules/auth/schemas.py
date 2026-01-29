"""Auth schemas for request/response validation."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    phone: Optional[str] = None
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "phone": "+919876543210",
                "first_name": "John",
                "last_name": "Doe",
            }
        }


class LoginRequest(BaseModel):
    """Email/password login request."""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
            }
        }


class OTPLoginRequest(BaseModel):
    """OTP login request."""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
            }
        }


class OTPVerifyRequest(BaseModel):
    """OTP verification request."""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    otp: str = Field(..., min_length=6, max_length=6)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "otp": "123456",
            }
        }


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    is_admin: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "token_type": "bearer",
                "expires_in": 1800,
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    """Email verification request."""
    token: str


class GoogleOAuthCallback(BaseModel):
    """Google OAuth callback."""
    code: str
    state: Optional[str] = None


class UserResponse(BaseModel):
    """User response (safe for client)."""
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    is_admin: bool
    email_verified: bool
    phone_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
