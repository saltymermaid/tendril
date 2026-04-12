"""Variety Pydantic schemas."""

from pydantic import BaseModel


class VarietyBase(BaseModel):
    name: str
    category_id: int
    season_override_start_month: int | None = None
    season_override_start_day: int | None = None
    season_override_end_month: int | None = None
    season_override_end_day: int | None = None
    days_to_germination_min: int | None = None
    days_to_germination_max: int | None = None
    days_to_harvest_min: int | None = None
    days_to_harvest_max: int | None = None
    seed_start_days: int | None = None
    planting_depth: str | None = None
    spacing: str = "1x1"
    sunlight: str | None = None
    is_climbing: bool = False
    planting_method: str = "both"
    seed_packet_photo_url: str | None = None
    source_url: str | None = None
    notes: str | None = None


class VarietyCreate(VarietyBase):
    pass


class VarietyUpdate(BaseModel):
    name: str | None = None
    category_id: int | None = None
    season_override_start_month: int | None = None
    season_override_start_day: int | None = None
    season_override_end_month: int | None = None
    season_override_end_day: int | None = None
    days_to_germination_min: int | None = None
    days_to_germination_max: int | None = None
    days_to_harvest_min: int | None = None
    days_to_harvest_max: int | None = None
    seed_start_days: int | None = None
    planting_depth: str | None = None
    spacing: str | None = None
    sunlight: str | None = None
    is_climbing: bool | None = None
    planting_method: str | None = None
    seed_packet_photo_url: str | None = None
    source_url: str | None = None
    notes: str | None = None


class VarietyResponse(VarietyBase):
    id: int
    user_id: int
    category_name: str | None = None
    category_color: str | None = None

    model_config = {"from_attributes": True}
