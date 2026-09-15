"""Builds the MCP server instance and its Streamable HTTP ASGI app.

No `auth=`/`token_verifier=` is passed to MCPServer/streamable_http_app — see
app/mcp/auth_middleware.py for why auth is handled outside the SDK instead.
"""

from mcp.server.mcpserver import MCPServer

from starlette.applications import Starlette

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

mcp_asgi_app: Starlette = mcp_server.streamable_http_app(streamable_http_path="/rpc")
