"""Per-request authenticated-user context for MCP tools.

Tools don't have access to FastAPI's `Depends(get_current_user)` — they're plain
functions invoked by the MCP session manager, not route handlers. `McpBearerAuthMiddleware`
(auth_middleware.py) sets this contextvar from the validated bearer token before the
request reaches the MCP app; every tool calls `get_mcp_user(db)` first, exactly mirroring
how every REST router calls `Depends(get_current_user)`.
"""

from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth import get_user_by_id

current_mcp_user_id: ContextVar[int | None] = ContextVar("current_mcp_user_id", default=None)


class McpAuthError(Exception):
    """Raised when a tool is invoked with no valid authenticated user in context."""


async def get_mcp_user(db: AsyncSession) -> User:
    """Resolve the authenticated user for the current MCP request, or raise McpAuthError."""
    user_id = current_mcp_user_id.get()
    if user_id is None:
        raise McpAuthError("Not authenticated")

    user = await get_user_by_id(db, user_id)
    if not user:
        raise McpAuthError("User not found")
    return user
