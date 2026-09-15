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


class PlantStartResponse(BaseModel):
    id: int
    user_id: int
    variety_id: int
    variety_name: str | None = None
    category_name: str | None = None
    category_color: str | None = None
    start_date: date
    quantity: int
    created_at: datetime

    model_config = {"from_attributes": True}
