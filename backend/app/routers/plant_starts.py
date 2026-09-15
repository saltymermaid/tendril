"""Plant Start CRUD router — started seedlings not yet assigned to a bed."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.plant_start import PlantStart
from app.models.user import User
from app.models.variety import Variety
from app.schemas.plant_start import PlantStartCreate, PlantStartResponse, PlantStartUpdate

router = APIRouter(prefix="/api/plant-starts", tags=["plant-starts"])


def _plant_start_to_response(start: PlantStart) -> PlantStartResponse:
    """Convert a PlantStart ORM object to PlantStartResponse, including variety/category info."""
    return PlantStartResponse(
        id=start.id,
        user_id=start.user_id,
        variety_id=start.variety_id,
        variety_name=start.variety.name if start.variety else None,
        category_name=start.variety.category.name if start.variety and start.variety.category else None,
        category_color=start.variety.category.color if start.variety and start.variety.category else None,
        start_date=start.start_date,
        quantity=start.quantity,
        created_at=start.created_at,
    )


@router.get("", response_model=list[PlantStartResponse])
async def list_plant_starts(
    include_used: bool = Query(default=False, description="Include starts with quantity 0"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List the current user's plant starts, newest first. Excludes used-up (quantity 0)
    starts unless include_used is set."""
    stmt = (
        select(PlantStart)
        .options(selectinload(PlantStart.variety).selectinload(Variety.category))
        .where(PlantStart.user_id == user.id)
        .order_by(PlantStart.start_date.desc())
    )

    if not include_used:
        stmt = stmt.where(PlantStart.quantity > 0)

    result = await db.execute(stmt)
    starts = result.scalars().all()

    return [_plant_start_to_response(s) for s in starts]


@router.post("", response_model=PlantStartResponse, status_code=status.HTTP_201_CREATED)
async def create_plant_start(
    data: PlantStartCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new plant start for the current user."""
    result = await db.execute(
        select(Variety).where(Variety.id == data.variety_id, Variety.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Variety not found")

    start = PlantStart(user_id=user.id, **data.model_dump())
    db.add(start)
    await db.commit()

    result = await db.execute(
        select(PlantStart)
        .options(selectinload(PlantStart.variety).selectinload(Variety.category))
        .where(PlantStart.id == start.id)
    )
    return _plant_start_to_response(result.scalar_one())


@router.put("/{start_id}", response_model=PlantStartResponse)
async def update_plant_start(
    start_id: int,
    data: PlantStartUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a plant start's variety, start date, and/or quantity."""
    result = await db.execute(
        select(PlantStart)
        .options(selectinload(PlantStart.variety).selectinload(Variety.category))
        .where(PlantStart.id == start_id, PlantStart.user_id == user.id)
    )
    start = result.scalar_one_or_none()
    if not start:
        raise HTTPException(status_code=404, detail="Plant Start not found")

    update_data = data.model_dump(exclude_unset=True)

    if "variety_id" in update_data and update_data["variety_id"] != start.variety_id:
        variety_result = await db.execute(
            select(Variety).where(Variety.id == update_data["variety_id"], Variety.user_id == user.id)
        )
        if not variety_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Variety not found")

    if "quantity" in update_data and update_data["quantity"] < 0:
        raise HTTPException(status_code=400, detail="quantity cannot be negative")

    for field, value in update_data.items():
        setattr(start, field, value)

    await db.commit()

    result = await db.execute(
        select(PlantStart)
        .options(selectinload(PlantStart.variety).selectinload(Variety.category))
        .where(PlantStart.id == start_id)
    )
    return _plant_start_to_response(result.scalar_one())


@router.delete("/{start_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plant_start(
    start_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a plant start (must belong to current user)."""
    result = await db.execute(
        select(PlantStart).where(PlantStart.id == start_id, PlantStart.user_id == user.id)
    )
    start = result.scalar_one_or_none()
    if not start:
        raise HTTPException(status_code=404, detail="Plant Start not found")

    await db.delete(start)
    await db.commit()
