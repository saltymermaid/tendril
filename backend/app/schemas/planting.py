"""Planting Pydantic schemas."""

from datetime import date

from pydantic import BaseModel


class PlantingBase(BaseModel):
    container_id: int
    variety_id: int
    square_x: int
    square_y: int
    square_width: int = 1
    square_height: int = 1
    tower_level: int | None = None
    start_date: date
    end_date: date
    planting_method: str | None = None  # direct_sow, transplant
    quantity: int | None = None


class PlantingCreate(PlantingBase):
    pass


class PlantingUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    planting_method: str | None = None
    quantity: int | None = None
    status: str | None = None  # not_started, in_progress, complete
    removal_reason: str | None = None


class PlantingResponse(BaseModel):
    id: int
    user_id: int
    container_id: int
    variety_id: int
    square_x: int
    square_y: int
    square_width: int
    square_height: int
    tower_level: int | None = None
    start_date: date
    end_date: date
    status: str
    planting_method: str | None = None
    quantity: int | None = None
    removal_reason: str | None = None

    # Joined fields
    variety_name: str | None = None
    category_name: str | None = None
    category_color: str | None = None
    container_name: str | None = None

    model_config = {"from_attributes": True}
