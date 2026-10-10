"""Category, PlantingSeason, and CompanionRule Pydantic schemas."""

from typing import Literal

from pydantic import BaseModel, Field

HarvestType = Literal["single", "continuous", "none"]


# --- Planting Season ---
class PlantingSeasonBase(BaseModel):
    usda_zone: str
    start_month: int
    start_day: int
    end_month: int
    end_day: int


class PlantingSeasonResponse(PlantingSeasonBase):
    id: int
    category_id: int

    model_config = {"from_attributes": True}


class PlantingSeasonCreate(PlantingSeasonBase):
    pass


# --- Companion Rule ---
class CompanionRuleResponse(BaseModel):
    id: int
    category_id: int
    companion_category_id: int
    companion_category_name: str | None = None
    companion_category_color: str | None = None
    relationship_type: str  # compatible/incompatible

    model_config = {"from_attributes": True}


# --- Category ---
class CategoryBase(BaseModel):
    name: str
    color: str
    harvest_type: HarvestType = "continuous"
    harvest_unit: str | None = None
    plants_per_square: int | None = Field(default=None, ge=1)
    icon_svg: str | None = None


class CategoryCreate(CategoryBase):
    planting_seasons: list[PlantingSeasonCreate] = []


class CategoryUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    harvest_type: HarvestType | None = None
    harvest_unit: str | None = None  # "" clears it
    plants_per_square: int | None = Field(default=None, ge=1)
    icon_svg: str | None = None
    planting_seasons: list[PlantingSeasonCreate] | None = None


class CategoryListResponse(BaseModel):
    id: int
    name: str
    color: str
    harvest_type: str
    harvest_unit: str | None = None
    plants_per_square: int | None = None
    icon_svg: str | None = None
    variety_count: int = 0

    model_config = {"from_attributes": True}


class CategoryDetailResponse(BaseModel):
    id: int
    name: str
    color: str
    harvest_type: str
    harvest_unit: str | None = None
    plants_per_square: int | None = None
    icon_svg: str | None = None
    planting_seasons: list[PlantingSeasonResponse] = []
    companion_rules: list[CompanionRuleResponse] = []

    model_config = {"from_attributes": True}
