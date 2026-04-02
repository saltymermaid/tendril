"""Events router — structured planting and harvest events."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.event import Event
from app.models.container import Container
from app.models.planting import Planting
from app.models.variety import Variety
from app.models.user import User
from app.schemas.event import EventCreate, EventResponse

router = APIRouter(prefix="/api/events", tags=["events"])

VALID_EVENT_TYPES = {"planting", "harvest"}
VALID_UNITS = {"lbs", "count", "bunches", "oz", "kg", "each"}


def _event_to_response(e: Event) -> EventResponse:
    """Convert an Event model to response, including joined names."""
    return EventResponse(
        id=e.id,
        user_id=e.user_id,
        event_type=e.event_type,
        date=e.date,
        container_id=e.container_id,
        planting_id=e.planting_id,
        variety_id=e.variety_id,
        square_x=e.square_x,
        square_y=e.square_y,
        tower_level=e.tower_level,
        quantity=e.quantity,
        unit=e.unit,
        notes=e.notes,
        created_at=e.created_at,
        container_name=e.container.name if e.container else None,
        variety_name=e.variety.name if e.variety else None,
        category_color=(
            e.variety.category.color
            if e.variety and e.variety.category
            else None
        ),
    )


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    body: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a structured event (planting or harvest)."""
    if body.event_type not in VALID_EVENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"event_type must be one of: {', '.join(VALID_EVENT_TYPES)}",
        )

    if body.event_type == "harvest":
        if not body.quantity or body.quantity <= 0:
            raise HTTPException(status_code=400, detail="Harvest events require a positive quantity")
        if body.unit and body.unit not in VALID_UNITS:
            raise HTTPException(
                status_code=400,
                detail=f"unit must be one of: {', '.join(VALID_UNITS)}",
            )

    # Validate container ownership if provided
    if body.container_id:
        result = await db.execute(
            select(Container).where(
                Container.id == body.container_id,
                Container.user_id == current_user.id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Container not found")

    # Validate planting ownership if provided
    if body.planting_id:
        result = await db.execute(
            select(Planting).where(
                Planting.id == body.planting_id,
                Planting.user_id == current_user.id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Planting not found")

    # Validate variety ownership if provided
    if body.variety_id:
        result = await db.execute(
            select(Variety).where(
                Variety.id == body.variety_id,
                Variety.user_id == current_user.id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Variety not found")

    event = Event(
        user_id=current_user.id,
        event_type=body.event_type,
        date=body.date,
        container_id=body.container_id,
        planting_id=body.planting_id,
        variety_id=body.variety_id,
        square_x=body.square_x,
        square_y=body.square_y,
        tower_level=body.tower_level,
        quantity=body.quantity,
        unit=body.unit,
        notes=body.notes,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    # Reload with relationships
    result = await db.execute(
        select(Event)
        .options(
            selectinload(Event.container),
            selectinload(Event.variety).selectinload(Variety.category),
        )
        .where(Event.id == event.id)
    )
    loaded = result.scalar_one()
    return _event_to_response(loaded)


@router.get("", response_model=list[EventResponse])
async def list_events(
    container_id: int | None = Query(None),
    planting_id: int | None = Query(None),
    variety_id: int | None = Query(None),
    event_type: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List events with optional filters."""
    query = (
        select(Event)
        .options(
            selectinload(Event.container),
            selectinload(Event.variety).selectinload(Variety.category),
        )
        .where(Event.user_id == current_user.id)
        .order_by(Event.date.desc(), Event.created_at.desc())
    )

    if container_id is not None:
        query = query.where(Event.container_id == container_id)
    if planting_id is not None:
        query = query.where(Event.planting_id == planting_id)
    if variety_id is not None:
        query = query.where(Event.variety_id == variety_id)
    if event_type is not None:
        query = query.where(Event.event_type == event_type)
    if start_date is not None:
        query = query.where(Event.date >= start_date)
    if end_date is not None:
        query = query.where(Event.date <= end_date)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    events = result.scalars().all()

    return [_event_to_response(e) for e in events]


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single event by ID."""
    result = await db.execute(
        select(Event)
        .options(
            selectinload(Event.container),
            selectinload(Event.variety).selectinload(Variety.category),
        )
        .where(Event.id == event_id, Event.user_id == current_user.id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_to_response(event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an event."""
    result = await db.execute(
        select(Event).where(Event.id == event_id, Event.user_id == current_user.id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.delete(event)
    await db.commit()
