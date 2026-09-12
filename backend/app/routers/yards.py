"""Yard CRUD router — per-user spatial garden layouts."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.container import Container
from app.models.user import User
from app.models.yard import Yard, YardObject
from app.schemas.yard import (
    YardCreate,
    YardDetailResponse,
    YardListResponse,
    YardObjectCreate,
    YardObjectResponse,
    YardObjectUpdate,
    YardUpdate,
)

router = APIRouter(prefix="/api/yards", tags=["yards"])

FEATURE_TYPES = {"path", "mulch", "building", "tree", "water", "other"}
OBJECT_TYPES = FEATURE_TYPES | {"bed"}


def _object_dims(obj: YardObject) -> tuple[int, int]:
    """Effective (width, height) for an object — derived from the container for beds."""
    if obj.object_type == "bed":
        return obj.container.width or 1, obj.container.height or 1
    return obj.square_width or 1, obj.square_height or 1


def _to_response(obj: YardObject) -> YardObjectResponse:
    width, height = _object_dims(obj)
    return YardObjectResponse(
        id=obj.id,
        yard_id=obj.yard_id,
        object_type=obj.object_type,
        container_id=obj.container_id,
        container_name=obj.container.name if obj.container else None,
        label=obj.label,
        square_x=obj.square_x,
        square_y=obj.square_y,
        square_width=width,
        square_height=height,
    )


def _rects_overlap(x1: int, y1: int, w1: int, h1: int, x2: int, y2: int, w2: int, h2: int) -> bool:
    return x1 < x2 + w2 and x2 < x1 + w1 and y1 < y2 + h2 and y2 < y1 + h1


async def _get_owned_yard(db: AsyncSession, yard_id: int, user: User, load_objects: bool = True) -> Yard:
    stmt = select(Yard).where(Yard.id == yard_id, Yard.user_id == user.id)
    if load_objects:
        stmt = stmt.options(selectinload(Yard.objects).selectinload(YardObject.container))
    result = await db.execute(stmt)
    yard = result.scalar_one_or_none()
    if not yard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yard not found")
    return yard


@router.get("", response_model=list[YardListResponse])
async def list_yards(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all yards for the current user."""
    stmt = select(Yard).where(Yard.user_id == user.id).order_by(Yard.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{yard_id}", response_model=YardDetailResponse)
async def get_yard(
    yard_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get yard detail with all placed objects."""
    yard = await _get_owned_yard(db, yard_id, user)
    return YardDetailResponse(
        id=yard.id,
        user_id=yard.user_id,
        name=yard.name,
        width=yard.width,
        height=yard.height,
        objects=[_to_response(o) for o in yard.objects],
    )


@router.post("", response_model=YardDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_yard(
    data: YardCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new yard."""
    if data.width < 1 or data.height < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yard width and height must be at least 1",
        )

    yard = Yard(user_id=user.id, name=data.name, width=data.width, height=data.height)
    db.add(yard)
    await db.commit()
    await db.refresh(yard)

    return await get_yard(yard.id, db, user)


@router.put("/{yard_id}", response_model=YardDetailResponse)
async def update_yard(
    yard_id: int,
    data: YardUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a yard's name or dimensions."""
    yard = await _get_owned_yard(db, yard_id, user)

    update_data = data.model_dump(exclude_unset=True)
    new_width = update_data.get("width", yard.width)
    new_height = update_data.get("height", yard.height)

    if new_width < 1 or new_height < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yard width and height must be at least 1",
        )

    if "width" in update_data or "height" in update_data:
        for obj in yard.objects:
            w, h = _object_dims(obj)
            if obj.square_x + w > new_width or obj.square_y + h > new_height:
                display_name = obj.label or (obj.container.name if obj.container else obj.object_type)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot resize — '{display_name}' no longer fits within the new bounds",
                )

    for field, value in update_data.items():
        setattr(yard, field, value)

    await db.commit()
    return await get_yard(yard_id, db, user)


@router.delete("/{yard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_yard(
    yard_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a yard (cascades placed objects, does not delete referenced containers)."""
    yard = await _get_owned_yard(db, yard_id, user, load_objects=False)
    await db.delete(yard)
    await db.commit()


@router.post(
    "/{yard_id}/objects",
    response_model=YardObjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_yard_object(
    yard_id: int,
    data: YardObjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Place an object (a bed, or a freeform feature) on the yard grid."""
    yard = await _get_owned_yard(db, yard_id, user)

    if data.object_type not in OBJECT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"object_type must be one of {sorted(OBJECT_TYPES)}",
        )

    container: Container | None = None
    if data.object_type == "bed":
        if not data.container_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="container_id is required to place a bed",
            )
        result = await db.execute(
            select(Container).where(
                Container.id == data.container_id, Container.user_id == user.id
            )
        )
        container = result.scalar_one_or_none()
        if not container:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Container not found")
        if container.type != "grid_bed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only grid beds can be placed in a yard",
            )
        width, height = container.width or 1, container.height or 1
    else:
        if data.container_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="container_id is only valid for object_type 'bed'",
            )
        if not data.square_width or not data.square_height:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="square_width and square_height are required for features",
            )
        width, height = data.square_width, data.square_height

    if (
        data.square_x < 0
        or data.square_y < 0
        or data.square_x + width > yard.width
        or data.square_y + height > yard.height
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Object does not fit within the {yard.width}x{yard.height} yard",
        )

    for existing in yard.objects:
        ew, eh = _object_dims(existing)
        if _rects_overlap(
            data.square_x, data.square_y, width, height,
            existing.square_x, existing.square_y, ew, eh,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Object overlaps an existing object in this yard",
            )

    obj = YardObject(
        yard_id=yard_id,
        object_type=data.object_type,
        container_id=data.container_id,
        label=data.label,
        square_x=data.square_x,
        square_y=data.square_y,
        square_width=None if data.object_type == "bed" else data.square_width,
        square_height=None if data.object_type == "bed" else data.square_height,
    )
    db.add(obj)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That bed is already placed in a yard",
        )
    await db.refresh(obj)
    obj.container = container
    return _to_response(obj)


@router.put("/{yard_id}/objects/{object_id}", response_model=YardObjectResponse)
async def update_yard_object(
    yard_id: int,
    object_id: int,
    data: YardObjectUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Reposition, resize, or relabel a placed object."""
    yard = await _get_owned_yard(db, yard_id, user)
    obj = next((o for o in yard.objects if o.id == object_id), None)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")

    update_data = data.model_dump(exclude_unset=True)

    if obj.object_type == "bed" and (
        "square_width" in update_data or "square_height" in update_data
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A bed's footprint follows its own dimensions and can't be overridden",
        )

    new_x = update_data.get("square_x", obj.square_x)
    new_y = update_data.get("square_y", obj.square_y)
    if obj.object_type == "bed":
        new_w, new_h = _object_dims(obj)
    else:
        new_w = update_data.get("square_width", obj.square_width)
        new_h = update_data.get("square_height", obj.square_height)

    if new_x < 0 or new_y < 0 or new_x + new_w > yard.width or new_y + new_h > yard.height:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Object does not fit within the {yard.width}x{yard.height} yard",
        )

    for existing in yard.objects:
        if existing.id == obj.id:
            continue
        ew, eh = _object_dims(existing)
        if _rects_overlap(
            new_x, new_y, new_w, new_h,
            existing.square_x, existing.square_y, ew, eh,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Object overlaps an existing object in this yard",
            )

    for field, value in update_data.items():
        setattr(obj, field, value)

    await db.commit()
    await db.refresh(obj)
    return _to_response(obj)


@router.delete("/{yard_id}/objects/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_yard_object(
    yard_id: int,
    object_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Remove an object from the yard (un-places a bed; does not delete the Container)."""
    yard = await _get_owned_yard(db, yard_id, user, load_objects=False)
    result = await db.execute(
        select(YardObject).where(YardObject.id == object_id, YardObject.yard_id == yard.id)
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")

    await db.delete(obj)
    await db.commit()
