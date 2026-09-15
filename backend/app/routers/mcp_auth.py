"""MCP OAuth router — hand-rolled authorization-code + PKCE flow for the Claude.ai connector.

This is a minimal, single-client OAuth 2.1 authorization server: the one client is
Tendril's own MCP connector (settings.mcp_client_id/secret, registered manually in
Claude.ai's connector "Advanced settings"). Being logged into Tendril via the existing
Google-OAuth browser session *is* the consent step — there's no separate consent screen,
consistent with ALLOWED_EMAILS already gating the whole app to one person.
"""

import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.services.auth import decode_token, get_user_by_id
from app.services.mcp_auth import (
    create_authorization_code,
    create_mcp_access_token,
    create_mcp_refresh_token,
    redeem_authorization_code,
    redeem_refresh_token,
    revoke_refresh_token,
    validate_resource_param,
    verify_pkce,
)

settings = get_settings()
router = APIRouter(prefix="/api/mcp", tags=["mcp-auth"])

SESSION_REDIRECT_KEY = "mcp_authorize_redirect"


@router.get("/authorize")
async def authorize(
    request: Request,
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    code_challenge: str = Query(...),
    code_challenge_method: str = Query(...),
    state: str | None = Query(default=None),
    resource: str | None = Query(default=None),
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Authorization endpoint. Requires an existing Tendril browser session (cookie);
    bounces through Google login first if none is present, then issues a code."""
    if response_type != "code":
        raise HTTPException(status_code=400, detail="response_type must be 'code'")
    if not secrets.compare_digest(client_id, settings.mcp_client_id):
        raise HTTPException(status_code=400, detail="Unknown client_id")
    if redirect_uri not in settings.mcp_allowed_redirect_uris_list:
        raise HTTPException(status_code=400, detail="redirect_uri not allowed")
    if code_challenge_method != "S256":
        raise HTTPException(status_code=400, detail="code_challenge_method must be S256")
    try:
        validate_resource_param(resource)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = None
    if access_token:
        payload = decode_token(access_token)
        if payload and payload.get("type") == "access":
            user = await get_user_by_id(db, int(payload["sub"]))

    if not user:
        # Stash the full incoming request so google_callback can bounce back here.
        request.session[SESSION_REDIRECT_KEY] = str(request.url)
        return RedirectResponse(url="/api/auth/login")

    code = await create_authorization_code(
        db=db,
        user_id=user.id,
        client_id=client_id,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )

    query = {"code": code}
    if state is not None:
        query["state"] = state
    separator = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(url=f"{redirect_uri}{separator}{urlencode(query)}")


@router.post("/token")
async def token(
    grant_type: str = Form(...),
    code: str | None = Form(default=None),
    redirect_uri: str | None = Form(default=None),
    code_verifier: str | None = Form(default=None),
    refresh_token: str | None = Form(default=None),
    resource: str | None = Form(default=None),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Token endpoint — exchanges an authorization code or refresh token for an access token."""
    if not secrets.compare_digest(client_id, settings.mcp_client_id) or not secrets.compare_digest(
        client_secret, settings.mcp_client_secret
    ):
        raise HTTPException(status_code=401, detail="invalid_client")
    try:
        validate_resource_param(resource)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if grant_type == "authorization_code":
        if not code or not redirect_uri or not code_verifier:
            raise HTTPException(status_code=400, detail="invalid_request")

        auth_code = await redeem_authorization_code(db, code)
        if not auth_code:
            raise HTTPException(status_code=400, detail="invalid_grant")
        if auth_code.redirect_uri != redirect_uri:
            raise HTTPException(status_code=400, detail="redirect_uri mismatch")
        if not verify_pkce(code_verifier, auth_code.code_challenge, auth_code.code_challenge_method):
            raise HTTPException(status_code=400, detail="invalid_grant")

        access = create_mcp_access_token(auth_code.user_id, client_id)
        refresh = await create_mcp_refresh_token(db, auth_code.user_id, client_id)

    elif grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(status_code=400, detail="invalid_request")

        row = await redeem_refresh_token(db, refresh_token)
        if not row:
            raise HTTPException(status_code=400, detail="invalid_grant")

        await revoke_refresh_token(db, row)
        access = create_mcp_access_token(row.user_id, client_id)
        refresh = await create_mcp_refresh_token(db, row.user_id, client_id)

    else:
        raise HTTPException(status_code=400, detail="unsupported_grant_type")

    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": settings.mcp_access_token_expire_minutes * 60,
        "refresh_token": refresh,
        "scope": "read write",
    }
