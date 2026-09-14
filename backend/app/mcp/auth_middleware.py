"""Bearer-token auth for the mounted MCP ASGI app.

A plain ASGI middleware rather than the `mcp` SDK's built-in `auth=`/`token_verifier=`
wiring: the SDK's own `.well-known/oauth-protected-resource` route is registered
*inside* the Streamable HTTP sub-app, so when that sub-app is mounted under a path
prefix (ours is at /api/mcp/rpc) the route ends up nested under the prefix instead of
at the true origin root that RFC 8615 requires. Handling auth entirely outside the SDK,
with hand-written root-level `.well-known` routes (app/routers/mcp_wellknown.py), avoids
that mismatch.

Error response shape mirrors mcp.server.auth.middleware.bearer_auth.RequireAuthMiddleware
for consistency with what an MCP client already expects to parse.
"""

import json
from datetime import datetime, timezone

from app.config import get_settings
from app.mcp.context import current_mcp_user_id
from app.services.mcp_auth import decode_mcp_token

settings = get_settings()


class McpBearerAuthMiddleware:
    """Wraps the MCP Streamable HTTP ASGI app, requiring a valid MCP access token."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        auth_header = headers.get(b"authorization", b"").decode("latin-1")

        payload = None
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
            payload = decode_mcp_token(token)
            if payload and payload.get("type") != "mcp_access":
                payload = None
            if payload and payload.get("exp") and payload["exp"] < datetime.now(timezone.utc).timestamp():
                payload = None

        if not payload:
            await self._send_auth_error(send)
            return

        auth_reset_token = current_mcp_user_id.set(int(payload["sub"]))
        try:
            await self.app(scope, receive, send)
        finally:
            current_mcp_user_id.reset(auth_reset_token)

    async def _send_auth_error(self, send) -> None:
        base = settings.base_url.rstrip("/") if settings.base_url else ""
        resource_metadata_url = f"{base}/.well-known/oauth-protected-resource/api/mcp/rpc"
        www_authenticate = (
            f'Bearer error="invalid_token", error_description="Authentication required", '
            f'resource_metadata="{resource_metadata_url}"'
        )
        body = json.dumps({"error": "invalid_token", "error_description": "Authentication required"}).encode()

        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                    (b"www-authenticate", www_authenticate.encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
