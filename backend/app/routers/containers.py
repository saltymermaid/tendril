"""Container CRUD router — per-user garden containers."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.container import Container, SquareSupport
from app.models.planting import Planting
from app.models.user import User
from app.schemas.container import (
    ContainerCreate,
    ContainerDetailResponse,
    ContainerListResponse,
    ContainerUpdate,
    SquareSupportCreate,
    SquareSupportResponse,
)

router = APIRouter(prefix="/api/containers", tags=["containers"])


@router.get("", response_model=list[ContainerListResponse])
async def list_containers(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all containers for the current user."""
    stmt = (
        select(Container)
        .where(Container.user_id == user.id)
        .order_by(Container.name)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{container_id}", response_model=ContainerDetailResponse)
async def get_container(
    container_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get container detail with support structures."""
    stmt = (
        select(Container)
        .options(selectinload(Container.square_supports))
        .where(Container.id == container_id, Container.user_id == user.id)
    )
    result = await db.execute(stmt)
    container = result.scalar_one_or_none()

    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    return container


@router.post("", response_model=ContainerDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_container(
    data: ContainerCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new container."""
    # Validate type-specific fields
    if data.type == "grid_bed":
        if not data.width or not data.height:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Grid beds require width and height",
            )
    elif data.type == "tower":
        if not data.levels or not data.pockets_per_level:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Towers require levels and pockets_per_level",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Container type must be 'grid_bed' or 'tower'",
        )

    container = Container(user_id=user.id, **data.model_dump())
    db.add(container)
    await db.commit()
    await db.refresh(container)

    return await get_container(container.id, db, user)


@router.put("/{container_id}", response_model=ContainerDetailResponse)
async def update_container(
    container_id: int,
    data: ContainerUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a container."""
    stmt = (
        select(Container)
        .where(Container.id == container_id, Container.user_id == user.id)
    )
    result = await db.execute(stmt)
    container = result.scalar_one_or_none()

    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(container, field, value)

    await db.commit()
    return await get_container(container_id, db, user)


@router.delete("/{container_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_container(
    container_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a container (only if no active plantings)."""
    stmt = (
        select(Container)
        .where(Container.id == container_id, Container.user_id == user.id)
    )
    result = await db.execute(stmt)
    container = result.scalar_one_or_none()

    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    # Check for active plantings
    active = await db.execute(
        select(Planting.id)
        .where(
            Planting.container_id == container_id,
            Planting.status.notin_(["removed", "finished"]),
        )
        .limit(1)
    )
    if active.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete container with active plantings",
        )

    await db.delete(container)
    await db.commit()


@router.put(
    "/{container_id}/squares/{x}/{y}/support",
    response_model=SquareSupportResponse,
)
async def set_square_support(
    container_id: int,
    x: int,
    y: int,
    data: SquareSupportCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Set or update support structure on a grid square."""
    # Verify container exists and is a grid bed
    stmt = (
        select(Container)
        .where(Container.id == container_id, Container.user_id == user.id)
    )
    result = await db.execute(stmt)
    container = result.scalar_one_or_none()

    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    if container.type != "grid_bed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Support structures are only for grid beds",
        )

    # Validate coordinates
    if x < 0 or x >= (container.width or 0) or y < 0 or y >= (container.height or 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Coordinates ({x}, {y}) out of bounds for {container.width}x{container.height} grid",
        )

    # Upsert support
    existing = await db.execute(
        select(SquareSupport).where(
            SquareSupport.container_id == container_id,
            SquareSupport.square_x == x,
            SquareSupport.square_y == y,
        )
    )
    support = existing.scalar_one_or_none()

    if support:
        support.support_type = data.support_type
    else:
        support = SquareSupport(
            container_id=container_id,
            square_x=x,
            square_y=y,
            support_type=data.support_type,
        )
        db.add(support)

    await db.commit()
    await db.refresh(support)
    return support


@router.delete(
    "/{container_id}/squares/{x}/{y}/support",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_square_support(
    container_id: int,
    x: int,
    y: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Remove support structure from a grid square."""
    # Verify container ownership
    stmt = (
        select(Container)
        .where(Container.id == container_id, Container.user_id == user.id)
    )
    result = await db.execute(stmt)
    container = result.scalar_one_or_none()

    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    existing = await db.execute(
        select(SquareSupport).where(
            SquareSupport.container_id == container_id,
            SquareSupport.square_x == x,
            SquareSupport.square_y == y,
        )
    )
    support = existing.scalar_one_or_none()

    if support:
        await db.delete(support)
        await db.commit()
