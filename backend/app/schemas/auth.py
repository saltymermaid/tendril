"""Auth-related Pydantic schemas."""

from pydantic import BaseModel, EmailStr


class DevLoginRequest(BaseModel):
    """Request body for dev login."""
    email: EmailStr


class UserResponse(BaseModel):
    """User info returned from /auth/me."""
    id: int
    email: str
    name: str
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


class AuthStatusResponse(BaseModel):
    """Response for auth status check."""
    authenticated: bool
    user: UserResponse | None = None
    dev_login_enabled: bool = False
