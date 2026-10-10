"""PlantStart Pydantic schemas."""

from datetime import date, datetime

from pydantic import BaseModel


class PlantStartCreate(BaseModel):
    variety_id: int
    start_date: date
    quantity: int = 1


class PlantStartUpdate(BaseModel):
    variety_id: int | None = None
    start_date: date | None = None
    quantity: int | None = None


class PlantStartAllocation(BaseModel):
    """A planting this start's seedlings were assigned to."""
    planting_id: int
    container_id: int
    container_name: str | None = None
    start_date: date  # When it goes (or went) into the ground
    status: str  # not_started (planned), in_progress, complete
    quantity: int


class PlantStartResponse(BaseModel):
    id: int
    user_id: int
    variety_id: int
    variety_name: str | None = None
    category_name: str | None = None
    category_color: str | None = None
    start_date: date
    quantity: int  # Available — not yet assigned to any bed
    planned_quantity: int = 0  # Reserved by planned plantings, still in the tray
    transplanted_quantity: int = 0  # Already in the ground
    total_quantity: int = 0  # available + planned + transplanted
    allocations: list[PlantStartAllocation] = []
    created_at: datetime

    model_config = {"from_attributes": True}
