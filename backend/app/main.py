"""Tendril API — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import get_settings
from app.mcp.auth_middleware import McpBearerAuthMiddleware
from app.mcp.server import mcp_asgi_app, mcp_server
from app.routers.auth import router as auth_router
from app.routers.categories import router as categories_router
from app.routers.containers import router as containers_router
from app.routers.events import router as events_router
from app.routers.mcp_auth import router as mcp_auth_router
from app.routers.mcp_wellknown import router as mcp_wellknown_router
from app.routers.notes import router as notes_router
from app.routers.plantings import router as plantings_router
from app.routers.recommendations import router as recommendations_router
from app.routers.settings import router as settings_router
from app.routers.tasks import router as tasks_router
from app.routers.varieties import router as varieties_router
from app.routers.weather import router as weather_router
from app.routers.push import router as push_router
from app.routers.yards import router as yards_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events.

    Mounting the MCP Streamable HTTP sub-app via app.mount() does not propagate ASGI
    lifespan events to it, so its session manager's task group is run explicitly here
    instead — the documented pattern for embedding an MCPServer in a larger app.
    """
    async with mcp_server.session_manager.run():
        yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Personal gardening planning and tracking API",
    version="0.1.0",
    lifespan=lifespan,
)

# Trust proxy headers from nginx (required for https:// redirect URIs behind Cloudflare Tunnel)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Session middleware (required for OAuth state parameter)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(containers_router)
app.include_router(events_router)
app.include_router(notes_router)
app.include_router(plantings_router)
app.include_router(recommendations_router)
app.include_router(settings_router)
app.include_router(tasks_router)
app.include_router(varieties_router)
app.include_router(weather_router)
app.include_router(push_router)
app.include_router(yards_router)
app.include_router(mcp_auth_router)
app.include_router(mcp_wellknown_router)

# MCP server for the Claude.ai connector, reachable at /api/mcp/rpc. Mounted at /api/mcp
# with the sub-app's own route at /rpc (rather than mounting at /api/mcp/rpc with the
# sub-app's route at /) so a request to exactly /api/mcp/rpc matches directly instead of
# 307-redirecting to add a trailing slash, which is Starlette's behavior when a mount's
# own root is requested with no trailing slash. Routes registered above (mcp_auth_router,
# mcp_wellknown_router) are matched first for their exact paths — Starlette checks routes
# in registration order — so this mount can't swallow /api/mcp/authorize or /api/mcp/token.
app.mount("/api/mcp", McpBearerAuthMiddleware(mcp_asgi_app))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name, "version": "0.1.0"}
