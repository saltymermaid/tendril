"""JournalNote Pydantic schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class NoteCreate(BaseModel):
    """Create a journal note."""

    content: str
    date: date
    container_id: Optional[int] = None
    planting_id: Optional[int] = None
    variety_id: Optional[int] = None
    square_x: Optional[int] = None
    square_y: Optional[int] = None
    tower_level: Optional[int] = None
    photo_url: Optional[str] = None


class NoteUpdate(BaseModel):
    """Update a journal note."""

    content: Optional[str] = None
    date: Optional[date] = None
    photo_url: Optional[str] = None


class NoteResponse(BaseModel):
    """Journal note response with all fields."""

    id: int
    user_id: int
    content: str
    date: date
    container_id: Optional[int]
    planting_id: Optional[int]
    variety_id: Optional[int]
    square_x: Optional[int]
    square_y: Optional[int]
    tower_level: Optional[int]
    photo_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Joined names for display
    container_name: Optional[str] = None
    variety_name: Optional[str] = None
    category_color: Optional[str] = None

    model_config = {"from_attributes": True}
