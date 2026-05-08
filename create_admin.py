import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.modules.users.models import User
from app.core.security import hash_password
from app.core.config import get_settings

async def create_admin():
    settings = get_settings()
    
    # Use the database URL from settings
    engine = create_async_engine(settings.POSTGRES_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # These will now pull the updated values from .env
    email = settings.ADMIN_EMAIL
    password = settings.ADMIN_PASSWORD
    
    async with async_session() as session:
        # Check if user already exists
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if user:
            print(f"User {email} already exists. Updating password and admin status.")
            user.password_hash = hash_password(password)
            user.is_admin = True
        else:
            print(f"Creating new admin user: {email}")
            user = User(
                email=email,
                password_hash=hash_password(password),
                first_name="System",
                last_name="Admin",
                is_admin=True,
                is_active=True,
                email_verified=True
            )
            session.add(user)
        
        await session.commit()
        print("Admin user setup complete.")

if __name__ == "__main__":
    asyncio.run(create_admin())
