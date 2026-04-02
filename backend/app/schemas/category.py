"""Category, PlantingSeason, and CompanionRule Pydantic schemas."""

from pydantic import BaseModel


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
    harvest_type: str = "continuous"
    icon_svg: str | None = None


class CategoryCreate(CategoryBase):
    planting_seasons: list[PlantingSeasonCreate] = []


class CategoryUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    harvest_type: str | None = None
    icon_svg: str | None = None
    planting_seasons: list[PlantingSeasonCreate] | None = None


class CategoryListResponse(BaseModel):
    id: int
    name: str
    color: str
    harvest_type: str
    icon_svg: str | None = None
    variety_count: int = 0

    model_config = {"from_attributes": True}


class CategoryDetailResponse(BaseModel):
    id: int
    name: str
    color: str
    harvest_type: str
    icon_svg: str | None = None
    planting_seasons: list[PlantingSeasonResponse] = []
    companion_rules: list[CompanionRuleResponse] = []

    model_config = {"from_attributes": True}
