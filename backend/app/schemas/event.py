"""Event Pydantic schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class EventCreate(BaseModel):
    """Create a structured event (planting or harvest)."""

    event_type: str  # planting, harvest
    date: date
    container_id: Optional[int] = None
    planting_id: Optional[int] = None
    variety_id: Optional[int] = None
    square_x: Optional[int] = None
    square_y: Optional[int] = None
    tower_level: Optional[int] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None  # lbs, count, bunches
    notes: Optional[str] = None


class EventResponse(BaseModel):
    """Event response with all fields."""

    id: int
    user_id: int
    event_type: str
    date: date
    container_id: Optional[int]
    planting_id: Optional[int]
    variety_id: Optional[int]
    square_x: Optional[int]
    square_y: Optional[int]
    tower_level: Optional[int]
    quantity: Optional[int]
    unit: Optional[str]
    notes: Optional[str]
    created_at: datetime

    # Joined names for display
    container_name: Optional[str] = None
    variety_name: Optional[str] = None
    category_color: Optional[str] = None

    model_config = {"from_attributes": True}
