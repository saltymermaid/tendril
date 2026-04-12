"""Variety CRUD router — per-user plant varieties."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.category import Category
from app.models.planting import Planting
from app.models.user import User
from app.models.variety import Variety
from app.schemas.variety import VarietyCreate, VarietyResponse, VarietyUpdate
from app.services.seed_packet_ai import extract_seed_packet_data

router = APIRouter(prefix="/api/varieties", tags=["varieties"])


# --- Schemas for photo extraction ---

class PhotoExtractRequest(BaseModel):
    image_base64: str
    media_type: str = "image/jpeg"


class PhotoExtractResponse(BaseModel):
    success: bool
    data: dict | None = None
    error: str | None = None


def _variety_to_response(variety: Variety) -> VarietyResponse:
    """Convert a Variety ORM model to a VarietyResponse, including category info."""
    return VarietyResponse(
        id=variety.id,
        user_id=variety.user_id,
        name=variety.name,
        category_id=variety.category_id,
        category_name=variety.category.name if variety.category else None,
        category_color=variety.category.color if variety.category else None,
        season_override_start_month=variety.season_override_start_month,
        season_override_start_day=variety.season_override_start_day,
        season_override_end_month=variety.season_override_end_month,
        season_override_end_day=variety.season_override_end_day,
        days_to_germination_min=variety.days_to_germination_min,
        days_to_germination_max=variety.days_to_germination_max,
        days_to_harvest_min=variety.days_to_harvest_min,
        days_to_harvest_max=variety.days_to_harvest_max,
        seed_start_days=variety.seed_start_days,
        planting_depth=variety.planting_depth,
        spacing=variety.spacing,
        sunlight=variety.sunlight,
        is_climbing=variety.is_climbing,
        planting_method=variety.planting_method,
        seed_packet_photo_url=variety.seed_packet_photo_url,
        source_url=variety.source_url,
        notes=variety.notes,
    )


@router.get("", response_model=list[VarietyResponse])
async def list_varieties(
    category_id: int | None = Query(default=None, description="Filter by category ID"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List the current user's varieties, optionally filtered by category."""
    stmt = (
        select(Variety)
        .options(selectinload(Variety.category))
        .where(Variety.user_id == user.id)
        .order_by(Variety.name)
    )

    if category_id is not None:
        stmt = stmt.where(Variety.category_id == category_id)

    result = await db.execute(stmt)
    varieties = result.scalars().all()

    return [_variety_to_response(v) for v in varieties]


@router.post("/extract-from-photo", response_model=PhotoExtractResponse)
async def extract_from_photo(
    body: PhotoExtractRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Extract seed packet data from a photo using Claude AI.

    Requires the user to have a Claude API key configured in settings.
    Accepts base64-encoded image data and returns extracted variety fields.
    """
    settings = current_user.settings or {}
    api_key = settings.get("claude_api_key")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Claude API key configured. Please add one in Settings.",
        )

    # Validate media type
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if body.media_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type: {body.media_type}. Use JPEG, PNG, GIF, or WebP.",
        )

    # Validate base64 data isn't too large (roughly 10MB limit)
    if len(body.image_base64) > 14_000_000:  # ~10MB in base64
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image too large. Please compress the image before uploading.",
        )

    result = await extract_seed_packet_data(
        image_base64=body.image_base64,
        media_type=body.media_type,
        api_key=api_key,
    )

    return PhotoExtractResponse(
        success=result.success,
        data=result.data,
        error=result.error,
    )


@router.get("/{variety_id}", response_model=VarietyResponse)
async def get_variety(
    variety_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single variety by ID (must belong to current user)."""
    stmt = (
        select(Variety)
        .options(selectinload(Variety.category))
        .where(Variety.id == variety_id, Variety.user_id == user.id)
    )
    result = await db.execute(stmt)
    variety = result.scalar_one_or_none()

    if not variety:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variety not found",
        )

    return _variety_to_response(variety)


@router.post("", response_model=VarietyResponse, status_code=status.HTTP_201_CREATED)
async def create_variety(
    data: VarietyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new variety for the current user."""
    # Verify category exists
    category = await db.get(Category, data.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {data.category_id} not found",
        )

    variety = Variety(
        user_id=user.id,
        **data.model_dump(),
    )
    db.add(variety)
    await db.commit()
    await db.refresh(variety)

    # Re-fetch with category relationship
    return await get_variety(variety.id, db, user)


@router.put("/{variety_id}", response_model=VarietyResponse)
async def update_variety(
    variety_id: int,
    data: VarietyUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a variety (must belong to current user)."""
    stmt = (
        select(Variety)
        .options(selectinload(Variety.category))
        .where(Variety.id == variety_id, Variety.user_id == user.id)
    )
    result = await db.execute(stmt)
    variety = result.scalar_one_or_none()

    if not variety:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variety not found",
        )

    # If changing category, verify it exists
    if data.category_id is not None and data.category_id != variety.category_id:
        category = await db.get(Category, data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {data.category_id} not found",
            )

    # Apply updates (only non-None fields)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(variety, field, value)

    await db.commit()

    # Re-fetch with category
    return await get_variety(variety_id, db, user)


@router.delete("/{variety_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variety(
    variety_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a variety (must belong to current user, no active plantings)."""
    stmt = (
        select(Variety)
        .where(Variety.id == variety_id, Variety.user_id == user.id)
    )
    result = await db.execute(stmt)
    variety = result.scalar_one_or_none()

    if not variety:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variety not found",
        )

    # Check for active plantings (status not in terminal states)
    active_plantings = await db.execute(
        select(Planting.id)
        .where(
            Planting.variety_id == variety_id,
            Planting.status.notin_(["removed", "finished"]),
        )
        .limit(1)
    )
    if active_plantings.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete variety with active plantings. Remove or finish all plantings first.",
        )

    await db.delete(variety)
    await db.commit()
