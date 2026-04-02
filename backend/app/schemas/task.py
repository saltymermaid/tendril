"""Task Pydantic schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    container_id: Optional[int] = None
    planting_id: Optional[int] = None
    variety_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None  # pending, completed, dismissed


class TaskResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    source: str
    status: str
    container_id: Optional[int] = None
    planting_id: Optional[int] = None
    variety_id: Optional[int] = None
    container_name: Optional[str] = None
    variety_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
