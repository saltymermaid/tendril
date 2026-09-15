"""Builds the MCP server instance and its Streamable HTTP ASGI app.

No `auth=`/`token_verifier=` is passed to MCPServer/streamable_http_app — see
app/mcp/auth_middleware.py for why auth is handled outside the SDK instead.
"""

from urllib.parse import urlparse

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from starlette.applications import Starlette

from app.config import get_settings

settings = get_settings()

mcp_server = MCPServer(
    name="tendril",
    instructions=(
        "Tools for reading and updating a personal square-foot-gardening plan in Tendril "
        "(USDA Zone 10a, St. Petersburg, FL — no frost, year-round growing). "
        "Prefer the list/get tools to answer questions before proposing changes, and use the "
        "narrow write tools (create_planting, complete_planting, create_task, update_task_status, "
        "create_plant_start) for changes — there is no delete or bulk-edit tool by design."
    ),
)

# Imported for their @mcp_server.tool() registration side effects. Must come after
# `mcp_server` is defined above, since both modules import it back from here.
from app.mcp import tools_read, tools_write  # noqa: F401,E402

# The SDK auto-enables DNS-rebinding protection (Host/Origin header allowlisting) whenever
# `host` isn't passed — its default (host="127.0.0.1") only allowlists localhost variants,
# which silently 421s every real request once this is deployed behind an actual domain.
# Passing our own TransportSecuritySettings keeps the protection on (still useful — it's
# independent of the bearer-token auth layer) while correctly allowlisting our real host too.
_allowed_hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
_allowed_origins = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]
if settings.base_url:
    _allowed_hosts.append(urlparse(settings.base_url).netloc)
    _allowed_origins.append(settings.base_url.rstrip("/"))

mcp_asgi_app: Starlette = mcp_server.streamable_http_app(
    streamable_http_path="/rpc",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=_allowed_hosts,
        allowed_origins=_allowed_origins,
    ),
)
