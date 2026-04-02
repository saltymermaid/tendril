"""Tendril API — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.routers.auth import router as auth_router
from app.routers.categories import router as categories_router
from app.routers.containers import router as containers_router
from app.routers.plantings import router as plantings_router
from app.routers.recommendations import router as recommendations_router
from app.routers.settings import router as settings_router
from app.routers.varieties import router as varieties_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    yield
    # Shutdown


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Personal gardening planning and tracking API",
    version="0.1.0",
    lifespan=lifespan,
)

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
app.include_router(plantings_router)
app.include_router(recommendations_router)
app.include_router(settings_router)
app.include_router(varieties_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name, "version": "0.1.0"}
