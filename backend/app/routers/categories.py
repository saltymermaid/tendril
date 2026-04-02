"""Category CRUD router — global shared data."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.category import Category, CompanionRule, PlantingSeason
from app.models.user import User
from app.models.variety import Variety
from app.schemas.category import (
    CategoryCreate,
    CategoryDetailResponse,
    CategoryListResponse,
    CategoryUpdate,
    CompanionRuleResponse,
    PlantingSeasonResponse,
)

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryListResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """List all categories with variety counts for the current user."""
    # Subquery for variety count per category for this user
    variety_count_sq = (
        select(Variety.category_id, func.count(Variety.id).label("variety_count"))
        .where(Variety.user_id == _user.id)
        .group_by(Variety.category_id)
        .subquery()
    )

    stmt = (
        select(
            Category.id,
            Category.name,
            Category.color,
            Category.harvest_type,
            Category.icon_svg,
            func.coalesce(variety_count_sq.c.variety_count, 0).label("variety_count"),
        )
        .outerjoin(variety_count_sq, Category.id == variety_count_sq.c.category_id)
        .order_by(Category.name)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        CategoryListResponse(
            id=row.id,
            name=row.name,
            color=row.color,
            harvest_type=row.harvest_type,
            icon_svg=row.icon_svg,
            variety_count=row.variety_count,
        )
        for row in rows
    ]


@router.get("/{category_id}", response_model=CategoryDetailResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Get category detail with planting seasons and companion rules."""
    stmt = (
        select(Category)
        .options(
            selectinload(Category.planting_seasons),
            selectinload(Category.companion_rules).selectinload(
                CompanionRule.companion_category
            ),
        )
        .where(Category.id == category_id)
    )
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Build companion rules with category names
    companion_rules = [
        CompanionRuleResponse(
            id=rule.id,
            category_id=rule.category_id,
            companion_category_id=rule.companion_category_id,
            companion_category_name=rule.companion_category.name if rule.companion_category else None,
            companion_category_color=rule.companion_category.color if rule.companion_category else None,
            relationship_type=rule.relationship_type,
        )
        for rule in category.companion_rules
    ]

    # Build planting seasons
    planting_seasons = [
        PlantingSeasonResponse(
            id=ps.id,
            category_id=ps.category_id,
            usda_zone=ps.usda_zone,
            start_month=ps.start_month,
            start_day=ps.start_day,
            end_month=ps.end_month,
            end_day=ps.end_day,
        )
        for ps in category.planting_seasons
    ]

    return CategoryDetailResponse(
        id=category.id,
        name=category.name,
        color=category.color,
        harvest_type=category.harvest_type,
        icon_svg=category.icon_svg,
        planting_seasons=planting_seasons,
        companion_rules=companion_rules,
    )


@router.post("", response_model=CategoryDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Create a new category with optional planting seasons."""
    # Check for duplicate name
    existing = await db.execute(select(Category).where(Category.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{data.name}' already exists",
        )

    category = Category(
        name=data.name,
        color=data.color,
        harvest_type=data.harvest_type,
        icon_svg=data.icon_svg,
    )
    db.add(category)
    await db.flush()  # Get the ID

    # Add planting seasons
    for ps_data in data.planting_seasons:
        ps = PlantingSeason(
            category_id=category.id,
            usda_zone=ps_data.usda_zone,
            start_month=ps_data.start_month,
            start_day=ps_data.start_day,
            end_month=ps_data.end_month,
            end_day=ps_data.end_day,
        )
        db.add(ps)

    await db.commit()
    await db.refresh(category)

    # Re-fetch with relationships
    return await get_category(category.id, db, _user)


@router.put("/{category_id}", response_model=CategoryDetailResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Update a category. Planting seasons are replaced if provided."""
    stmt = (
        select(Category)
        .options(selectinload(Category.planting_seasons))
        .where(Category.id == category_id)
    )
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Update scalar fields
    if data.name is not None:
        # Check for duplicate name (excluding self)
        existing = await db.execute(
            select(Category).where(Category.name == data.name, Category.id != category_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{data.name}' already exists",
            )
        category.name = data.name
    if data.color is not None:
        category.color = data.color
    if data.harvest_type is not None:
        category.harvest_type = data.harvest_type
    if data.icon_svg is not None:
        category.icon_svg = data.icon_svg

    # Replace planting seasons if provided
    if data.planting_seasons is not None:
        # Delete existing seasons
        for ps in category.planting_seasons:
            await db.delete(ps)

        # Add new seasons
        for ps_data in data.planting_seasons:
            ps = PlantingSeason(
                category_id=category.id,
                usda_zone=ps_data.usda_zone,
                start_month=ps_data.start_month,
                start_day=ps_data.start_day,
                end_month=ps_data.end_month,
                end_day=ps_data.end_day,
            )
            db.add(ps)

    await db.commit()

    # Re-fetch with relationships
    return await get_category(category_id, db, _user)


@router.post("/{category_id}/icon", response_model=CategoryDetailResponse)
async def upload_category_icon(
    category_id: int,
    icon_data: dict,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Upload/update SVG icon for a category. Expects {"svg": "<svg>...</svg>"}."""
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    svg = icon_data.get("svg")
    if not svg or not isinstance(svg, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must include 'svg' field with SVG markup string",
        )

    category.icon_svg = svg
    await db.commit()

    return await get_category(category_id, db, _user)
