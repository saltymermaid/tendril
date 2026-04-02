"""Plantings router — CRUD with overlap prevention."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.container import Container
from app.models.planting import Planting
from app.models.user import User
from app.models.variety import Variety
from app.schemas.planting import PlantingCreate, PlantingResponse, PlantingUpdate

router = APIRouter(prefix="/api/plantings", tags=["plantings"])


def _planting_to_response(p: Planting) -> PlantingResponse:
    """Convert a Planting ORM object to PlantingResponse with joined fields."""
    variety_name = None
    category_name = None
    category_color = None
    container_name = None

    if p.variety:
        variety_name = p.variety.name
        if p.variety.category:
            category_name = p.variety.category.name
            category_color = p.variety.category.color

    if p.container:
        container_name = p.container.name

    return PlantingResponse(
        id=p.id,
        user_id=p.user_id,
        container_id=p.container_id,
        variety_id=p.variety_id,
        square_x=p.square_x,
        square_y=p.square_y,
        square_width=p.square_width,
        square_height=p.square_height,
        tower_level=p.tower_level,
        start_date=p.start_date,
        end_date=p.end_date,
        status=p.status,
        planting_method=p.planting_method,
        quantity=p.quantity,
        removal_reason=p.removal_reason,
        variety_name=variety_name,
        category_name=category_name,
        category_color=category_color,
        container_name=container_name,
    )


async def _check_overlap(
    db: AsyncSession,
    user_id: int,
    container_id: int,
    square_x: int,
    square_y: int,
    square_width: int,
    square_height: int,
    start_date: date,
    end_date: date,
    exclude_planting_id: int | None = None,
) -> None:
    """Check for overlapping plantings on the same squares in the same date range.

    A planting occupies squares from (square_x, square_y) to
    (square_x + square_width - 1, square_y + square_height - 1).
    Two plantings overlap if their square ranges intersect AND their date ranges overlap.
    """
    # Build query for plantings in the same container that overlap in date range
    query = select(Planting).where(
        Planting.user_id == user_id,
        Planting.container_id == container_id,
        # Date overlap: existing.start < new.end AND existing.end > new.start
        Planting.start_date < end_date,
        Planting.end_date > start_date,
    )

    if exclude_planting_id:
        query = query.where(Planting.id != exclude_planting_id)

    result = await db.execute(query)
    existing_plantings = result.scalars().all()

    # Check spatial overlap for each existing planting
    new_x_min, new_x_max = square_x, square_x + square_width - 1
    new_y_min, new_y_max = square_y, square_y + square_height - 1

    for existing in existing_plantings:
        ex_x_min = existing.square_x
        ex_x_max = existing.square_x + existing.square_width - 1
        ex_y_min = existing.square_y
        ex_y_max = existing.square_y + existing.square_height - 1

        # Check if rectangles overlap
        if (
            new_x_min <= ex_x_max
            and new_x_max >= ex_x_min
            and new_y_min <= ex_y_max
            and new_y_max >= ex_y_min
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Overlap with existing planting (id={existing.id}) "
                f"at ({existing.square_x},{existing.square_y}) "
                f"from {existing.start_date} to {existing.end_date}",
            )


# --- Create planting ---
@router.post("", response_model=PlantingResponse, status_code=status.HTTP_201_CREATED)
async def create_planting(
    body: PlantingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new planting with overlap prevention."""
    # Validate container belongs to user
    result = await db.execute(
        select(Container).where(
            Container.id == body.container_id,
            Container.user_id == current_user.id,
        )
    )
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    # Validate variety belongs to user
    result = await db.execute(
        select(Variety).where(
            Variety.id == body.variety_id,
            Variety.user_id == current_user.id,
        )
    )
    variety = result.scalar_one_or_none()
    if not variety:
        raise HTTPException(status_code=404, detail="Variety not found")

    # Validate dates
    if body.end_date <= body.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    # Validate square bounds for grid_bed
    if container.type == "grid_bed":
        if (
            body.square_x < 0
            or body.square_y < 0
            or body.square_x + body.square_width > container.width
            or body.square_y + body.square_height > container.height
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Planting extends beyond container bounds "
                f"({container.width}x{container.height})",
            )

    # Validate tower level
    if container.type == "tower":
        if body.tower_level is None:
            raise HTTPException(status_code=400, detail="tower_level required for tower containers")
        if body.tower_level < 0 or body.tower_level >= container.levels:
            raise HTTPException(
                status_code=400,
                detail=f"tower_level must be 0-{container.levels - 1}",
            )

    # Check for overlapping plantings
    await _check_overlap(
        db=db,
        user_id=current_user.id,
        container_id=body.container_id,
        square_x=body.square_x,
        square_y=body.square_y,
        square_width=body.square_width,
        square_height=body.square_height,
        start_date=body.start_date,
        end_date=body.end_date,
    )

    planting = Planting(
        user_id=current_user.id,
        container_id=body.container_id,
        variety_id=body.variety_id,
        square_x=body.square_x,
        square_y=body.square_y,
        square_width=body.square_width,
        square_height=body.square_height,
        tower_level=body.tower_level,
        start_date=body.start_date,
        end_date=body.end_date,
        planting_method=body.planting_method,
        quantity=body.quantity,
        status="not_started",
    )
    db.add(planting)
    await db.commit()
    await db.refresh(planting)

    # Reload with relationships
    result = await db.execute(
        select(Planting)
        .options(
            selectinload(Planting.variety).selectinload(Variety.category),
            selectinload(Planting.container),
        )
        .where(Planting.id == planting.id)
    )
    planting = result.scalar_one()
    return _planting_to_response(planting)


# --- Get plantings for a container ---
@router.get("/by-container/{container_id}", response_model=list[PlantingResponse])
async def get_container_plantings(
    container_id: int,
    as_of: date | None = Query(None, description="Filter plantings active on this date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all plantings for a container, optionally filtered by date."""
    # Verify container belongs to user
    result = await db.execute(
        select(Container).where(
            Container.id == container_id,
            Container.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Container not found")

    query = (
        select(Planting)
        .options(
            selectinload(Planting.variety).selectinload(Variety.category),
            selectinload(Planting.container),
        )
        .where(
            Planting.user_id == current_user.id,
            Planting.container_id == container_id,
        )
        .order_by(Planting.start_date)
    )

    if as_of:
        query = query.where(
            Planting.start_date <= as_of,
            Planting.end_date > as_of,
        )

    result = await db.execute(query)
    plantings = result.scalars().all()
    return [_planting_to_response(p) for p in plantings]


# --- Get planting detail ---
@router.get("/{planting_id}", response_model=PlantingResponse)
async def get_planting(
    planting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single planting by ID."""
    result = await db.execute(
        select(Planting)
        .options(
            selectinload(Planting.variety).selectinload(Variety.category),
            selectinload(Planting.container),
        )
        .where(
            Planting.id == planting_id,
            Planting.user_id == current_user.id,
        )
    )
    planting = result.scalar_one_or_none()
    if not planting:
        raise HTTPException(status_code=404, detail="Planting not found")
    return _planting_to_response(planting)


# --- Update planting ---
@router.put("/{planting_id}", response_model=PlantingResponse)
async def update_planting(
    planting_id: int,
    body: PlantingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a planting (dates, method, quantity, status)."""
    result = await db.execute(
        select(Planting)
        .options(
            selectinload(Planting.variety).selectinload(Variety.category),
            selectinload(Planting.container),
        )
        .where(
            Planting.id == planting_id,
            Planting.user_id == current_user.id,
        )
    )
    planting = result.scalar_one_or_none()
    if not planting:
        raise HTTPException(status_code=404, detail="Planting not found")

    update_data = body.model_dump(exclude_unset=True)

    # If dates are changing, re-check overlap
    new_start = update_data.get("start_date", planting.start_date)
    new_end = update_data.get("end_date", planting.end_date)
    if new_end <= new_start:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    if "start_date" in update_data or "end_date" in update_data:
        await _check_overlap(
            db=db,
            user_id=current_user.id,
            container_id=planting.container_id,
            square_x=planting.square_x,
            square_y=planting.square_y,
            square_width=planting.square_width,
            square_height=planting.square_height,
            start_date=new_start,
            end_date=new_end,
            exclude_planting_id=planting.id,
        )

    for key, value in update_data.items():
        setattr(planting, key, value)

    await db.commit()
    await db.refresh(planting)

    # Reload with relationships
    result = await db.execute(
        select(Planting)
        .options(
            selectinload(Planting.variety).selectinload(Variety.category),
            selectinload(Planting.container),
        )
        .where(Planting.id == planting.id)
    )
    planting = result.scalar_one()
    return _planting_to_response(planting)


# --- Delete planting ---
@router.delete("/{planting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_planting(
    planting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a planting. Only allowed for not_started plantings."""
    result = await db.execute(
        select(Planting).where(
            Planting.id == planting_id,
            Planting.user_id == current_user.id,
        )
    )
    planting = result.scalar_one_or_none()
    if not planting:
        raise HTTPException(status_code=404, detail="Planting not found")

    if planting.status != "not_started":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete planting with status '{planting.status}'. "
            "Only 'not_started' plantings can be deleted.",
        )

    await db.delete(planting)
    await db.commit()
