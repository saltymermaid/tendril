"""MCP OAuth service — authorization codes, PKCE, and access/refresh tokens for the Claude.ai connector.

Kept entirely separate from services/auth.py: MCP tokens are signed with their own
secret (MCP_TOKEN_SECRET) and carry a distinct `type` claim, so they can never be
confused with — or substituted for — the browser session's access_token/refresh_token
cookies.
"""

import hashlib
import secrets
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.mcp_auth import McpAuthorizationCode, McpRefreshToken

settings = get_settings()

ALGORITHM = "HS256"
MCP_ACCESS_TOKEN_TYPE = "mcp_access"
MCP_REFRESH_TOKEN_TYPE = "mcp_refresh"


def canonical_resource_url() -> str:
    """The MCP server's own canonical resource URI (RFC 8707 / MCP auth spec).

    Tendril has exactly one MCP resource, so this is a fixed value rather than
    something tracked per authorization/token grant.
    """
    return f"{settings.base_url.rstrip('/')}/api/mcp/rpc"


def validate_resource_param(resource: str | None) -> None:
    """Validate an OAuth `resource` parameter against our one canonical resource URI.

    The MCP spec requires clients to send `resource` on both the authorization and
    token requests, and requires servers to validate it (RFC 8707). Raises ValueError
    with a message suitable for an `invalid_target` error response if it doesn't match.
    A missing `resource` is accepted for backwards compatibility with older clients,
    but the issued token is still audience-bound to our one resource regardless.
    """
    if resource is not None and resource.rstrip("/") != canonical_resource_url():
        raise ValueError(f"resource must be {canonical_resource_url()}")


def create_mcp_access_token(user_id: int, client_id: str) -> str:
    """Create a short-lived MCP access token (stateless JWT, verified on every /api/mcp/rpc call).

    Always carries `aud` bound to our one canonical resource URI, per the MCP spec's
    audience-validation requirement — independent of whether the client sent `resource`.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.mcp_access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "client_id": client_id,
        "type": MCP_ACCESS_TOKEN_TYPE,
        "scope": "read write",
        "aud": canonical_resource_url(),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.mcp_token_secret, algorithm=ALGORITHM)


async def create_mcp_refresh_token(db: AsyncSession, user_id: int, client_id: str) -> str:
    """Create a long-lived MCP refresh token, backed by a revocable DB row."""
    jti = secrets.token_urlsafe(32)
    expire = datetime.now(timezone.utc) + timedelta(days=settings.mcp_refresh_token_expire_days)

    db.add(
        McpRefreshToken(
            jti=jti,
            user_id=user_id,
            client_id=client_id,
            expires_at=expire,
        )
    )
    await db.flush()

    payload = {
        "sub": str(user_id),
        "client_id": client_id,
        "type": MCP_REFRESH_TOKEN_TYPE,
        "jti": jti,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.mcp_token_secret, algorithm=ALGORITHM)


def decode_mcp_token(token: str) -> dict | None:
    """Decode and validate an MCP JWT. Returns payload or None if invalid/expired.

    Audience (`aud`) is deliberately not checked here via PyJWT's built-in `audience=`
    kwarg — that requires every caller to know and pass the expected audience, but this
    function also decodes refresh tokens, which carry no `aud` at all. Callers that need
    audience validation (the bearer middleware, for access tokens) check `payload["aud"]`
    themselves after calling this.
    """
    try:
        return jwt.decode(
            token, settings.mcp_token_secret, algorithms=[ALGORITHM], options={"verify_aud": False}
        )
    except jwt.InvalidTokenError:
        return None


async def redeem_refresh_token(db: AsyncSession, token: str) -> McpRefreshToken | None:
    """Validate a refresh token JWT against its DB row. Does not revoke it — caller rotates."""
    payload = decode_mcp_token(token)
    if not payload or payload.get("type") != MCP_REFRESH_TOKEN_TYPE:
        return None

    jti = payload.get("jti")
    if not jti:
        return None

    result = await db.execute(select(McpRefreshToken).where(McpRefreshToken.jti == jti))
    row = result.scalar_one_or_none()
    if not row or row.revoked_at is not None:
        return None
    if row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None

    return row


async def revoke_refresh_token(db: AsyncSession, row: McpRefreshToken) -> None:
    """Mark a refresh token row revoked (used on rotation and on invalid-reuse detection)."""
    row.revoked_at = datetime.now(timezone.utc)
    await db.flush()


async def create_authorization_code(
    db: AsyncSession,
    user_id: int,
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    code_challenge_method: str,
) -> str:
    """Issue a single-use, short-lived authorization code."""
    code = secrets.token_urlsafe(48)
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.mcp_auth_code_expire_seconds)

    db.add(
        McpAuthorizationCode(
            code=code,
            user_id=user_id,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            expires_at=expire,
        )
    )
    await db.flush()
    return code


async def redeem_authorization_code(db: AsyncSession, code: str) -> McpAuthorizationCode | None:
    """Look up an authorization code and mark it used (single-use enforcement).

    Returns None if the code doesn't exist, was already used, or has expired.
    Caller is responsible for verifying PKCE and redirect_uri against the returned row.
    """
    result = await db.execute(select(McpAuthorizationCode).where(McpAuthorizationCode.code == code))
    row = result.scalar_one_or_none()
    if not row or row.used_at is not None:
        return None
    if row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None

    row.used_at = datetime.now(timezone.utc)
    await db.flush()
    return row


def verify_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
    """Verify a PKCE code_verifier against the stored code_challenge. Only S256 is accepted."""
    if method != "S256":
        return False
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    computed = urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return secrets.compare_digest(computed, code_challenge)
