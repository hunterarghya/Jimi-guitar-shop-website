"""Auth service - business logic for authentication."""
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_otp,
    generate_verification_token,
)
from app.core.config import get_settings
from app.middleware import AppException
from app.modules.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    OTPVerifyRequest,
    TokenResponse,
)
import logging
import json

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service."""

    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.settings = get_settings()

    async def register(self, req: RegisterRequest) -> dict:
        """Register new user."""
        # Check if user exists
        from app.modules.users.models import User

        existing = await self.db.execute(
            select(User).where(User.email == req.email)
        )
        if existing.scalars().first():
            raise AppException("Email already registered", 409)

        # Create user
        user = User(
            email=req.email,
            password_hash=hash_password(req.password),
            first_name=req.first_name,
            last_name=req.last_name,
            phone=req.phone,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()

        # Generate verification token
        verification_token = generate_verification_token()
        await self.redis.setex(
            f"email_verify:{user.id}",
            3600,  # 1 hour
            verification_token,
        )

        # Send verification email (would be async task in production)
        logger.info(f"Verification email sent to {req.email}")

        await self.db.commit()

        return {
            "user_id": str(user.id),
            "email": user.email,
            "message": "Registration successful. Please verify your email.",
        }

    async def login(self, req: LoginRequest) -> TokenResponse:
        """Login with email and password."""
        from app.modules.users.models import User

        # Check rate limit
        rate_key = f"login_attempts:{req.email}"
        attempts = await self.redis.incr(rate_key)

        if attempts == 1:
            await self.redis.expire(rate_key, 300)  # 5 minutes

        if attempts > 5:
            raise AppException("Too many login attempts. Try again later.", 429)

        # Find user
        result = await self.db.execute(
            select(User).where(User.email == req.email)
        )
        user = result.scalars().first()

        if not user or not verify_password(req.password, user.password_hash):
            raise AppException("Invalid email or password", 401)

        # Clear rate limit on successful login
        await self.redis.delete(rate_key)

        # Generate tokens
        tokens = await self._create_tokens(user)

        # Store refresh token in Redis for revocation
        await self.redis.setex(
            f"refresh_token:{tokens['refresh_token']}",
            self.settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            json.dumps({"user_id": str(user.id)}),
        )

        return TokenResponse(**tokens)

    async def login_with_otp(self, email: str, phone: Optional[str] = None) -> dict:
        """Send OTP for login."""
        from app.modules.users.models import User

        # Find user
        if email:
            result = await self.db.execute(
                select(User).where(User.email == email)
            )
        elif phone:
            result = await self.db.execute(
                select(User).where(User.phone == phone)
            )
        else:
            raise AppException("Email or phone required", 400)

        user = result.scalars().first()
        if not user:
            raise AppException("User not found", 404)

        # Generate and store OTP
        otp = generate_otp()
        contact = email or phone
        await self.redis.setex(
            f"otp_login:{contact}",
            600,  # 10 minutes
            json.dumps({"otp": otp, "user_id": str(user.id)}),
        )

        logger.info(f"OTP sent to {contact}: {otp}")

        return {
            "message": "OTP sent successfully",
            "contact": contact,
        }

    async def verify_otp_login(self, req: OTPVerifyRequest) -> TokenResponse:
        """Verify OTP and login."""
        contact = req.email or req.phone
        otp_key = f"otp_login:{contact}"

        # Retrieve OTP
        otp_data = await self.redis.get(otp_key)
        if not otp_data:
            raise AppException("OTP expired", 400)

        data = json.loads(otp_data)
        if data["otp"] != req.otp:
            raise AppException("Invalid OTP", 401)

        # Get user
        from app.modules.users.models import User

        result = await self.db.execute(
            select(User).where(User.id == data["user_id"])
        )
        user = result.scalars().first()

        if not user:
            raise AppException("User not found", 404)

        # Mark as verified
        if req.email:
            user.email_verified = True
        elif req.phone:
            user.phone_verified = True

        await self.db.commit()
        await self.redis.delete(otp_key)

        # Generate tokens
        tokens = await self._create_tokens(user)

        return TokenResponse(**tokens)

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token."""
        # Check if refresh token is revoked
        revoke_key = f"revoked_token:{refresh_token}"
        if await self.redis.exists(revoke_key):
            raise AppException("Token revoked", 401)

        # Verify refresh token
        payload = verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AppException("Invalid refresh token", 401)

        user_id = payload.get("sub")

        from app.modules.users.models import User

        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalars().first()

        if not user or not user.is_active:
            raise AppException("User not found or inactive", 401)

        # Generate new access token
        tokens = await self._create_tokens(user)

        return TokenResponse(**tokens)

    async def logout(self, access_token: str, refresh_token: str) -> dict:
        """Logout user by revoking tokens."""
        # Add tokens to JTI blocklist
        payload = verify_token(access_token)
        if payload:
            exp = payload.get("exp")
            if exp:
                ttl = max(0, int(exp) - int(datetime.now(timezone.utc).timestamp()))
                if ttl > 0:
                    await self.redis.setex(
                        f"revoked_token:{access_token}",
                        ttl,
                        "1",
                    )

        # Also revoke refresh token
        await self.redis.setex(
            f"revoked_token:{refresh_token}",
            self.settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            "1",
        )

        logger.info(f"User {payload.get('sub')} logged out")

        return {"message": "Logged out successfully"}

    async def _create_tokens(self, user) -> dict:
        """Create access and refresh tokens."""
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "is_admin": user.is_admin,
            }
        )

        refresh_token = create_refresh_token(
            data={
                "sub": str(user.id),
            }
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "is_admin": user.is_admin,
        }

    async def verify_email(self, token: str, user_id: str) -> dict:
        """Verify email with token."""
        stored_token = await self.redis.get(f"email_verify:{user_id}")

        if not stored_token or stored_token != token:
            raise AppException("Invalid or expired verification token", 401)

        from app.modules.users.models import User

        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalars().first()

        if not user:
            raise AppException("User not found", 404)

        user.email_verified = True
        await self.db.commit()
        await self.redis.delete(f"email_verify:{user_id}")

        return {"message": "Email verified successfully"}
