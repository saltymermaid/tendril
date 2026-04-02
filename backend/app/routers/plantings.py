"""Plantings router — CRUD with overlap prevention and lifecycle management."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.container import Container
from app.models.planting import Planting
from app.models.user import User
from app.models.variety import Variety
from app.schemas.planting import (
    ActivatePlanting,
    CompletePlanting,
    LifecyclePhaseResponse,
    PlantingCreate,
    PlantingResponse,
    PlantingUpdate,
)
from app.services.lifecycle import compute_lifecycle_phase, _avg_days

router = APIRouter(prefix="/api/plantings", tags=["plantings"])


def _compute_lifecycle(p: Planting) -> LifecyclePhaseResponse | None:
    """Compute lifecycle phase for a planting using its variety data."""
    variety = p.variety
    phase = compute_lifecycle_phase(
        status=p.status,
        start_date=p.start_date,
        end_date=p.end_date,
        days_to_germination_min=variety.days_to_germination_min if variety else None,
        days_to_germination_max=variety.days_to_germination_max if variety else None,
        days_to_harvest_min=variety.days_to_harvest_min if variety else None,
        days_to_harvest_max=variety.days_to_harvest_max if variety else None,
    )
    return LifecyclePhaseResponse(
        phase=phase.phase,
        phase_display=phase.phase_display,
        day_number=phase.day_number,
        total_days=phase.total_days,
        phase_day=phase.phase_day,
        phase_total_days=phase.phase_total_days,
        progress_percent=phase.progress_percent,
    )


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
        lifecycle=_compute_lifecycle(p),
    )


async def _load_planting_with_relations(db: AsyncSession, planting_id: int) -> Planting | None:
    """Load a planting with variety, category, and container relationships."""
    result = await db.execute(
        select(Planting)
        .options(
            selectinload(Planting.variety).selectinload(Variety.category),
            selectinload(Planting.container),
        )
        .where(Planting.id == planting_id)
    )
    return result.scalar_one_or_none()


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
    query = select(Planting).where(
        Planting.user_id == user_id,
        Planting.container_id == container_id,
        Planting.start_date < end_date,
        Planting.end_date > start_date,
    )

    if exclude_planting_id:
        query = query.where(Planting.id != exclude_planting_id)

    result = await db.execute(query)
    existing_plantings = result.scalars().all()

    new_x_min, new_x_max = square_x, square_x + square_width - 1
    new_y_min, new_y_max = square_y, square_y + square_height - 1

    for existing in existing_plantings:
        ex_x_min = existing.square_x
        ex_x_max = existing.square_x + existing.square_width - 1
        ex_y_min = existing.square_y
        ex_y_max = existing.square_y + existing.square_height - 1

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
    result = await db.execute(
        select(Container).where(
            Container.id == body.container_id,
            Container.user_id == current_user.id,
        )
    )
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    result = await db.execute(
        select(Variety).where(
            Variety.id == body.variety_id,
            Variety.user_id == current_user.id,
        )
    )
    variety = result.scalar_one_or_none()
    if not variety:
        raise HTTPException(status_code=404, detail="Variety not found")

    if body.end_date <= body.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

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

    if container.type == "tower":
        if body.tower_level is None:
            raise HTTPException(status_code=400, detail="tower_level required for tower containers")
        if body.tower_level < 0 or body.tower_level >= container.levels:
            raise HTTPException(
                status_code=400,
                detail=f"tower_level must be 0-{container.levels - 1}",
            )

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

    loaded = await _load_planting_with_relations(db, planting.id)
    return _planting_to_response(loaded)


# --- Timeline endpoint for Gantt chart ---
@router.get("/timeline")
async def get_timeline(
    start_date: date = Query(..., description="Timeline start date"),
    end_date: date = Query(..., description="Timeline end date"),
    container_id: int | None = Query(None, description="Filter to specific container"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get plantings with lifecycle phase boundaries for Gantt chart rendering.

    Returns plantings that overlap with the given date range, including
    computed phase boundaries (germination_end, harvest_start) for each.
    """
    query = (
        select(Planting)
        .options(
            selectinload(Planting.variety).selectinload(Variety.category),
            selectinload(Planting.container),
        )
        .where(
            Planting.user_id == current_user.id,
            # Planting overlaps with the requested range
            Planting.start_date <= end_date,
            Planting.end_date >= start_date,
        )
        .order_by(Planting.start_date)
    )

    if container_id is not None:
        query = query.where(Planting.container_id == container_id)

    result = await db.execute(query)
    plantings = result.scalars().all()

    timeline_items = []
    for p in plantings:
        variety = p.variety
        germ_days = _avg_days(
            variety.days_to_germination_min if variety else None,
            variety.days_to_germination_max if variety else None,
            default=7,
        )
        harvest_days = _avg_days(
            variety.days_to_harvest_min if variety else None,
            variety.days_to_harvest_max if variety else None,
            default=60,
        )

        germination_end = (p.start_date + timedelta(days=germ_days)).isoformat()
        harvest_start = (p.start_date + timedelta(days=harvest_days)).isoformat()

        timeline_items.append({
            "id": p.id,
            "container_id": p.container_id,
            "container_name": p.container.name if p.container else None,
            "variety_id": p.variety_id,
            "variety_name": variety.name if variety else None,
            "category_name": variety.category.name if variety and variety.category else None,
            "category_color": variety.category.color if variety and variety.category else None,
            "start_date": p.start_date.isoformat(),
            "end_date": p.end_date.isoformat(),
            "germination_end": germination_end,
            "harvest_start": harvest_start,
            "status": p.status,
            "square_x": p.square_x,
            "square_y": p.square_y,
            "tower_level": p.tower_level,
        })

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "container_id": container_id,
        "total": len(timeline_items),
        "plantings": timeline_items,
    }


# --- Get plantings for a container ---
@router.get("/by-container/{container_id}", response_model=list[PlantingResponse])
async def get_container_plantings(
    container_id: int,
    as_of: date | None = Query(None, description="Filter plantings active on this date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all plantings for a container, optionally filtered by date."""
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

    loaded = await _load_planting_with_relations(db, planting.id)
    return _planting_to_response(loaded)


# --- Activate planting (Not Started → In Progress) ---
@router.post("/{planting_id}/activate", response_model=PlantingResponse)
async def activate_planting(
    planting_id: int,
    body: ActivatePlanting | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition a planting from Not Started to In Progress.

    Optionally set the actual start date (defaults to today).
    If the start date changes, re-checks overlap.
    """
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
            detail=f"Cannot activate planting with status '{planting.status}'. "
            "Only 'not_started' plantings can be activated.",
        )

    actual_start = date.today()
    if body and body.actual_start_date:
        actual_start = body.actual_start_date

    # If start date is changing, re-check overlap
    if actual_start != planting.start_date:
        if actual_start >= planting.end_date:
            raise HTTPException(
                status_code=400,
                detail="actual_start_date must be before end_date",
            )
        await _check_overlap(
            db=db,
            user_id=current_user.id,
            container_id=planting.container_id,
            square_x=planting.square_x,
            square_y=planting.square_y,
            square_width=planting.square_width,
            square_height=planting.square_height,
            start_date=actual_start,
            end_date=planting.end_date,
            exclude_planting_id=planting.id,
        )
        planting.start_date = actual_start

    planting.status = "in_progress"
    await db.commit()
    await db.refresh(planting)

    loaded = await _load_planting_with_relations(db, planting.id)
    return _planting_to_response(loaded)


# --- Complete planting (In Progress → Complete) ---
@router.post("/{planting_id}/complete", response_model=PlantingResponse)
async def complete_planting(
    planting_id: int,
    body: CompletePlanting,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition a planting from In Progress to Complete.

    Requires a removal reason. Optionally set the actual end date (defaults to today).
    """
    result = await db.execute(
        select(Planting).where(
            Planting.id == planting_id,
            Planting.user_id == current_user.id,
        )
    )
    planting = result.scalar_one_or_none()
    if not planting:
        raise HTTPException(status_code=404, detail="Planting not found")

    if planting.status != "in_progress":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete planting with status '{planting.status}'. "
            "Only 'in_progress' plantings can be completed.",
        )

    valid_reasons = {"harvest_complete", "died", "pulled_early", "pest_disease", "other"}
    if body.removal_reason not in valid_reasons:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid removal_reason. Must be one of: {', '.join(sorted(valid_reasons))}",
        )

    actual_end = date.today()
    if body.actual_end_date:
        actual_end = body.actual_end_date

    if actual_end < planting.start_date:
        raise HTTPException(
            status_code=400,
            detail="actual_end_date must be on or after start_date",
        )

    planting.end_date = actual_end
    planting.status = "complete"
    planting.removal_reason = body.removal_reason
    await db.commit()
    await db.refresh(planting)

    loaded = await _load_planting_with_relations(db, planting.id)
    return _planting_to_response(loaded)


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
