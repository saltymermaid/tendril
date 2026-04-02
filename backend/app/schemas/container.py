"""Container and SquareSupport Pydantic schemas."""

from pydantic import BaseModel


# --- Square Support ---
class SquareSupportBase(BaseModel):
    square_x: int
    square_y: int
    support_type: str  # trellis, cage, pole


class SquareSupportResponse(SquareSupportBase):
    id: int
    container_id: int

    model_config = {"from_attributes": True}


class SquareSupportCreate(BaseModel):
    support_type: str  # trellis, cage, pole


# --- Container ---
class ContainerBase(BaseModel):
    name: str
    type: str  # grid_bed / tower
    location_description: str | None = None
    width: int | None = None
    height: int | None = None
    levels: int | None = None
    pockets_per_level: int | None = None
    irrigation_type: str | None = None
    irrigation_duration_minutes: int | None = None
    irrigation_frequency: str | None = None


class ContainerCreate(ContainerBase):
    pass


class ContainerUpdate(BaseModel):
    name: str | None = None
    location_description: str | None = None
    width: int | None = None
    height: int | None = None
    levels: int | None = None
    pockets_per_level: int | None = None
    irrigation_type: str | None = None
    irrigation_duration_minutes: int | None = None
    irrigation_frequency: str | None = None


class ContainerListResponse(BaseModel):
    id: int
    name: str
    type: str
    location_description: str | None = None
    width: int | None = None
    height: int | None = None
    levels: int | None = None
    pockets_per_level: int | None = None
    irrigation_type: str | None = None

    model_config = {"from_attributes": True}


class ContainerDetailResponse(ContainerBase):
    id: int
    user_id: int
    square_supports: list[SquareSupportResponse] = []

    model_config = {"from_attributes": True}
