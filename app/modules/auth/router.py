"""Auth router - API endpoints."""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.core import get_db, get_redis
from app.core.security import verify_token
from app.middleware import AppException
from app.modules.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    OTPLoginRequest,
    OTPVerifyRequest,
    TokenResponse,
    RefreshTokenRequest,
    VerifyEmailRequest,
)
from app.modules.auth.service import AuthService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=dict)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Register a new user."""
    service = AuthService(db, redis)
    return await service.register(req)


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Login with email and password."""
    service = AuthService(db, redis)
    return await service.login(req)


@router.post("/login-otp/request", response_model=dict)
async def request_otp_login(
    req: OTPLoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Request OTP for login."""
    if not req.email and not req.phone:
        raise AppException("Email or phone required", 400)

    service = AuthService(db, redis)
    return await service.login_with_otp(req.email, req.phone)


@router.post("/login-otp/verify", response_model=TokenResponse)
async def verify_otp_login(
    req: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Verify OTP and login."""
    service = AuthService(db, redis)
    return await service.verify_otp_login(req)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    req: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Refresh access token."""
    service = AuthService(db, redis)
    return await service.refresh_access_token(req.refresh_token)


@router.post("/logout", response_model=dict)
async def logout(
    authorization: str = Header(None),
    refresh_token: str = Header(None),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Logout user."""
    if not authorization or not refresh_token:
        raise AppException("Missing authorization header", 401)

    access_token = authorization.replace("Bearer ", "")
    service = AuthService(db, redis)
    return await service.logout(access_token, refresh_token)


@router.post("/verify-email", response_model=dict)
async def verify_email(
    req: VerifyEmailRequest,
    user_id: str = Header(None),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Verify email."""
    if not user_id:
        raise AppException("User ID required", 400)

    service = AuthService(db, redis)
    return await service.verify_email(req.token, user_id)

