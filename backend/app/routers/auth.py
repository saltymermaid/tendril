"""Authentication router — Google OAuth, dev login, JWT management."""

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import AuthStatusResponse, DevLoginRequest, UserResponse
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_or_create_user,
    get_user_by_id,
    is_email_allowed,
)

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])

# --- Google OAuth setup ---
oauth = OAuth()
if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


def _set_auth_cookies(response: Response, user_id: int, session_timeout_hours: int | None = None) -> None:
    """Set access and refresh token cookies on the response.

    *session_timeout_hours* overrides the site-wide default when the user has
    configured a custom session timeout in their settings.
    """
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id, hours=session_timeout_hours)

    # Compute refresh cookie max_age from hours or fall back to site default
    if session_timeout_hours is not None:
        refresh_max_age = session_timeout_hours * 3600
    else:
        refresh_max_age = settings.refresh_token_expire_days * 86400

    # secure=True in production (HTTPS via Cloudflare Tunnel); False only in local dev
    secure = not settings.debug

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=refresh_max_age,
        path="/api/auth",  # Only sent to auth endpoints
    )


def _clear_auth_cookies(response: Response) -> None:
    """Clear auth cookies."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/auth")


# --- Auth status (public) ---
@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(
    db: AsyncSession = Depends(get_db),
    access_token: str | None = Cookie(default=None),
):
    """Check authentication status. Returns user info if authenticated."""
    user = None
    if access_token:
        payload = decode_token(access_token)
        if payload and payload.get("type") == "access":
            user_id = int(payload["sub"])
            user = await get_user_by_id(db, user_id)

    return AuthStatusResponse(
        authenticated=user is not None,
        user=UserResponse.model_validate(user) if user else None,
        dev_login_enabled=settings.enable_dev_login,
    )


# --- Google OAuth ---
@router.get("/login")
async def google_login(request: Request):
    """Redirect to Google OAuth consent screen."""
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured",
        )
    if settings.base_url:
        # Explicit base URL avoids http:// when behind Cloudflare Tunnel
        redirect_uri = settings.base_url.rstrip("/") + "/api/auth/callback"
    else:
        redirect_uri = str(request.url_for("google_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def google_callback(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback."""
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured",
        )

    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth authorization failed",
        )

    userinfo = token.get("userinfo")
    if not userinfo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve user info from Google",
        )

    email = userinfo.get("email", "")
    if not is_email_allowed(email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Email {email} is not authorized to use this application",
        )

    user = await get_or_create_user(
        db=db,
        email=email,
        name=userinfo.get("name", ""),
        google_id=userinfo.get("sub"),
        avatar_url=userinfo.get("picture"),
    )

    timeout_hours: int | None = (user.settings or {}).get("session_timeout_hours")
    _set_auth_cookies(response, user.id, session_timeout_hours=timeout_hours)

    # Redirect to frontend after successful login
    response.status_code = status.HTTP_302_FOUND
    response.headers["location"] = "/"
    return response


# --- Dev login ---
@router.post("/dev-login", response_model=UserResponse)
async def dev_login(
    body: DevLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Dev-only login: create/find user by email and issue JWT without OAuth.

    Only available when ENABLE_DEV_LOGIN=true.
    """
    if not settings.enable_dev_login:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    user = await get_or_create_user(
        db=db,
        email=body.email,
        name=body.email.split("@")[0],
    )

    timeout_hours: int | None = (user.settings or {}).get("session_timeout_hours")
    _set_auth_cookies(response, user.id, session_timeout_hours=timeout_hours)
    return UserResponse.model_validate(user)


# --- Current user ---
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return UserResponse.model_validate(current_user)


# --- Token refresh ---
@router.post("/refresh", response_model=UserResponse)
async def refresh_tokens(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
):
    """Refresh the access token using the refresh token cookie."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = int(payload["sub"])
    user = await get_user_by_id(db, user_id)
    if not user:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    timeout_hours: int | None = (user.settings or {}).get("session_timeout_hours")
    _set_auth_cookies(response, user.id, session_timeout_hours=timeout_hours)
    return UserResponse.model_validate(user)


# --- Logout ---
@router.post("/logout")
async def logout(response: Response):
    """Clear auth cookies to log out."""
    _clear_auth_cookies(response)
    return {"message": "Logged out"}
