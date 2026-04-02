"""Notes router — free-form journal notes."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.journal_note import JournalNote
from app.models.container import Container
from app.models.planting import Planting
from app.models.variety import Variety
from app.models.user import User
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse

router = APIRouter(prefix="/api/notes", tags=["notes"])


def _note_to_response(n: JournalNote) -> NoteResponse:
    """Convert a JournalNote model to response, including joined names."""
    return NoteResponse(
        id=n.id,
        user_id=n.user_id,
        content=n.content,
        date=n.date,
        container_id=n.container_id,
        planting_id=n.planting_id,
        variety_id=n.variety_id,
        square_x=n.square_x,
        square_y=n.square_y,
        tower_level=n.tower_level,
        photo_url=n.photo_url,
        created_at=n.created_at,
        updated_at=n.updated_at,
        container_name=n.container.name if n.container else None,
        variety_name=n.variety.name if n.variety else None,
        category_color=(
            n.variety.category.color
            if n.variety and n.variety.category
            else None
        ),
    )


async def _load_note(db: AsyncSession, note_id: int) -> JournalNote | None:
    """Load a note with relationships."""
    result = await db.execute(
        select(JournalNote)
        .options(
            selectinload(JournalNote.container),
            selectinload(JournalNote.variety).selectinload(Variety.category),
        )
        .where(JournalNote.id == note_id)
    )
    return result.scalar_one_or_none()


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    body: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a journal note."""
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

    note = JournalNote(
        user_id=current_user.id,
        content=body.content,
        date=body.date,
        container_id=body.container_id,
        planting_id=body.planting_id,
        variety_id=body.variety_id,
        square_x=body.square_x,
        square_y=body.square_y,
        tower_level=body.tower_level,
        photo_url=body.photo_url,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    loaded = await _load_note(db, note.id)
    return _note_to_response(loaded)


@router.get("", response_model=list[NoteResponse])
async def list_notes(
    container_id: int | None = Query(None),
    planting_id: int | None = Query(None),
    variety_id: int | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List journal notes with optional filters."""
    query = (
        select(JournalNote)
        .options(
            selectinload(JournalNote.container),
            selectinload(JournalNote.variety).selectinload(Variety.category),
        )
        .where(JournalNote.user_id == current_user.id)
        .order_by(JournalNote.date.desc(), JournalNote.created_at.desc())
    )

    if container_id is not None:
        query = query.where(JournalNote.container_id == container_id)
    if planting_id is not None:
        query = query.where(JournalNote.planting_id == planting_id)
    if variety_id is not None:
        query = query.where(JournalNote.variety_id == variety_id)
    if start_date is not None:
        query = query.where(JournalNote.date >= start_date)
    if end_date is not None:
        query = query.where(JournalNote.date <= end_date)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    notes = result.scalars().all()

    return [_note_to_response(n) for n in notes]


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single note by ID."""
    result = await db.execute(
        select(JournalNote)
        .options(
            selectinload(JournalNote.container),
            selectinload(JournalNote.variety).selectinload(Variety.category),
        )
        .where(JournalNote.id == note_id, JournalNote.user_id == current_user.id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return _note_to_response(note)


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    body: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a journal note."""
    result = await db.execute(
        select(JournalNote).where(
            JournalNote.id == note_id,
            JournalNote.user_id == current_user.id,
        )
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(note, key, value)

    await db.commit()
    await db.refresh(note)

    loaded = await _load_note(db, note.id)
    return _note_to_response(loaded)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a journal note."""
    result = await db.execute(
        select(JournalNote).where(
            JournalNote.id == note_id,
            JournalNote.user_id == current_user.id,
        )
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(note)
    await db.commit()
