"""Yard and YardObject Pydantic schemas."""

from pydantic import BaseModel


# --- Yard Object ---
class YardObjectBase(BaseModel):
    object_type: str  # bed, path, mulch, building, tree, water, other
    container_id: int | None = None
    label: str | None = None
    square_x: int
    square_y: int
    square_width: int | None = None
    square_height: int | None = None


class YardObjectCreate(YardObjectBase):
    pass


class YardObjectUpdate(BaseModel):
    label: str | None = None
    square_x: int | None = None
    square_y: int | None = None
    square_width: int | None = None
    square_height: int | None = None


class YardObjectResponse(BaseModel):
    id: int
    yard_id: int
    object_type: str
    container_id: int | None = None
    container_name: str | None = None
    label: str | None = None
    square_x: int
    square_y: int
    square_width: int
    square_height: int

    model_config = {"from_attributes": True}


# --- Yard ---
class YardBase(BaseModel):
    name: str
    width: int
    height: int


class YardCreate(YardBase):
    pass


class YardUpdate(BaseModel):
    name: str | None = None
    width: int | None = None
    height: int | None = None


class YardListResponse(BaseModel):
    id: int
    name: str
    width: int
    height: int

    model_config = {"from_attributes": True}


class YardDetailResponse(YardBase):
    id: int
    user_id: int
    objects: list[YardObjectResponse] = []

    model_config = {"from_attributes": True}
