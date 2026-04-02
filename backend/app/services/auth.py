"""Authentication service — JWT token management and user operations."""

from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User

settings = get_settings()

ALGORITHM = "HS256"


def create_access_token(user_id: int) -> str:
    """Create a short-lived access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: int, hours: int | None = None) -> str:
    """Create a long-lived refresh token.

    If *hours* is provided (user's configured session timeout), use that;
    otherwise fall back to the site-wide ``refresh_token_expire_days`` setting.
    """
    if hours is not None:
        expire = datetime.now(timezone.utc) + timedelta(hours=hours)
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_or_create_user(
    db: AsyncSession,
    email: str,
    name: str = "",
    google_id: str | None = None,
    avatar_url: str | None = None,
) -> User:
    """Find existing user by email or create a new one."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        # Update fields if provided
        if google_id and not user.google_id:
            user.google_id = google_id
        if name and not user.name:
            user.name = name
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        await db.flush()
        return user

    # Create new user
    user = User(
        email=email,
        name=name or email.split("@")[0],
        google_id=google_id,
        avatar_url=avatar_url,
        settings={},
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Get a user by their ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def is_email_allowed(email: str) -> bool:
    """Check if an email is in the allowed whitelist. Empty whitelist = all allowed."""
    allowed = settings.allowed_emails_list
    if not allowed:
        return True
    return email.lower() in [e.lower() for e in allowed]
