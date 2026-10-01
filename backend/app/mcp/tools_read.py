"""Read-only MCP tools — mirror the query logic of the equivalent REST routers.

Every tool opens its own session (tools aren't route handlers, so there's no
`Depends(get_db)`) and scopes every query by the authenticated user's id, exactly like
the REST routers do. Dates/datetimes are converted to ISO strings explicitly rather than
relying on the tool-result serializer to know how.
"""

from datetime import date

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mcp.server.mcpserver.exceptions import ToolError

from app.config import get_settings
from app.database import async_session
from app.mcp.server import mcp_server
from app.mcp.context import get_mcp_user
from app.models.category import Category, CompanionRule
from app.models.container import Container
from app.models.plant_start import PlantStart
from app.models.planting import Planting
from app.models.task import Task
from app.models.variety import Variety
from app.models.yard import Yard, YardObject
from app.services.lifecycle import compute_lifecycle_phase
from app.services.recommendations import get_recommendations as _get_recommendations

DEFAULT_LIST_LIMIT = 100


def _iso(value):
    return value.isoformat() if value is not None else None


def _local_iso(value):
    """Render a UTC-aware datetime as an ISO string in the app's local timezone."""
    if value is None:
        return None
    from zoneinfo import ZoneInfo

    return value.astimezone(ZoneInfo(get_settings().app_timezone)).isoformat()


def _variety_dict(v: Variety) -> dict:
    return {
        "id": v.id,
        "name": v.name,
        "category_id": v.category_id,
        "category_name": v.category.name if v.category else None,
        "days_to_germination_min": v.days_to_germination_min,
        "days_to_germination_max": v.days_to_germination_max,
        "days_to_harvest_min": v.days_to_harvest_min,
        "days_to_harvest_max": v.days_to_harvest_max,
        "seed_start_days": v.seed_start_days,
        "planting_depth": v.planting_depth,
        "spacing": v.spacing,
        "sunlight": v.sunlight,
        "is_climbing": v.is_climbing,
        "planting_method": v.planting_method,
        "notes": v.notes,
    }


@mcp_server.tool()
async def list_varieties(category_id: int | None = None, limit: int = DEFAULT_LIST_LIMIT) -> list[dict]:
    """List the user's plant varieties, optionally filtered by category."""
    async with async_session() as db:
        user = await get_mcp_user(db)
        stmt = (
            select(Variety)
            .options(selectinload(Variety.category))
            .where(Variety.user_id == user.id)
            .order_by(Variety.name)
            .limit(limit)
        )
        if category_id is not None:
            stmt = stmt.where(Variety.category_id == category_id)
        result = await db.execute(stmt)
        return [_variety_dict(v) for v in result.scalars().all()]


def _category_dict(c: Category) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "color": c.color,
        "harvest_type": c.harvest_type,
        "icon_svg": c.icon_svg,
        "planting_seasons": [
            {
                "id": ps.id,
                "usda_zone": ps.usda_zone,
                "start_month": ps.start_month,
                "start_day": ps.start_day,
                "end_month": ps.end_month,
                "end_day": ps.end_day,
            }
            for ps in c.planting_seasons
        ],
        "companion_rules": [
            {
                "id": r.id,
                "companion_category_id": r.companion_category_id,
                "companion_category_name": r.companion_category.name if r.companion_category else None,
                "relationship_type": r.relationship_type,
            }
            for r in c.companion_rules
        ],
    }


async def _get_category_detail(db: AsyncSession, category_id: int) -> Category | None:
    """Shared by get_category and the create/update category write tools so all three
    return the same shape."""
    stmt = (
        select(Category)
        .options(
            selectinload(Category.planting_seasons),
            selectinload(Category.companion_rules).selectinload(CompanionRule.companion_category),
        )
        .where(Category.id == category_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@mcp_server.tool()
async def list_categories() -> list[dict]:
    """List all plant categories (global, shared across every user of this Tendril
    instance — e.g. Tomatoes, Peppers), with the count of the current user's varieties
    in each. Look here for a category's id before creating or filtering a variety.
    Omits icon_svg (some categories carry large hand-drawn icons) — call get_category
    for a specific category's full icon markup."""
    async with async_session() as db:
        user = await get_mcp_user(db)
        variety_count_sq = (
            select(Variety.category_id, func.count(Variety.id).label("variety_count"))
            .where(Variety.user_id == user.id)
            .group_by(Variety.category_id)
            .subquery()
        )
        stmt = (
            select(
                Category.id,
                Category.name,
                Category.color,
                Category.harvest_type,
                Category.icon_svg.isnot(None).label("has_icon"),
                func.coalesce(variety_count_sq.c.variety_count, 0).label("variety_count"),
            )
            .outerjoin(variety_count_sq, Category.id == variety_count_sq.c.category_id)
            .order_by(Category.name)
        )
        result = await db.execute(stmt)
        return [
            {
                "id": row.id,
                "name": row.name,
                "color": row.color,
                "harvest_type": row.harvest_type,
                "has_icon": row.has_icon,
                "variety_count": row.variety_count,
            }
            for row in result.all()
        ]


@mcp_server.tool()
async def get_category(category_id: int) -> dict:
    """Get a category's detail, including its Zone 10a planting seasons and companion
    planting rules with other categories."""
    async with async_session() as db:
        await get_mcp_user(db)
        category = await _get_category_detail(db, category_id)
        if not category:
            raise ToolError(f"Category {category_id} not found")
        return _category_dict(category)


def _plant_start_dict(s: PlantStart) -> dict:
    return {
        "id": s.id,
        "variety_id": s.variety_id,
        "variety_name": s.variety.name if s.variety else None,
        "start_date": _iso(s.start_date),
        "quantity": s.quantity,
    }


@mcp_server.tool()
async def list_plant_starts(include_used: bool = False, limit: int = DEFAULT_LIST_LIMIT) -> list[dict]:
    """List the user's plant starts (started seedlings not yet assigned to a bed), newest
    first. Excludes used-up (quantity 0) starts unless include_used is set."""
    async with async_session() as db:
        user = await get_mcp_user(db)
        stmt = (
            select(PlantStart)
            .options(selectinload(PlantStart.variety))
            .where(PlantStart.user_id == user.id)
            .order_by(PlantStart.start_date.desc())
            .limit(limit)
        )
        if not include_used:
            stmt = stmt.where(PlantStart.quantity > 0)
        result = await db.execute(stmt)
        return [_plant_start_dict(s) for s in result.scalars().all()]


@mcp_server.tool()
async def get_variety(variety_id: int) -> dict:
    """Get a single variety by id."""
    async with async_session() as db:
        user = await get_mcp_user(db)
        stmt = (
            select(Variety)
            .options(selectinload(Variety.category))
            .where(Variety.id == variety_id, Variety.user_id == user.id)
        )
        result = await db.execute(stmt)
        variety = result.scalar_one_or_none()
        if not variety:
            raise ToolError(f"Variety {variety_id} not found")
        return _variety_dict(variety)


def _container_dict(c: Container) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "type": c.type,
        "location_description": c.location_description,
        "width": c.width,
        "height": c.height,
        "levels": c.levels,
        "pockets_per_level": c.pockets_per_level,
        "irrigation_type": c.irrigation_type,
        "irrigation_duration_minutes": c.irrigation_duration_minutes,
        "irrigation_frequency": c.irrigation_frequency,
    }


@mcp_server.tool()
async def list_containers(container_type: str | None = None) -> list[dict]:
    """List the user's containers (grid beds and towers). Filter with container_type='grid_bed' or 'tower'."""
    async with async_session() as db:
        user = await get_mcp_user(db)
        stmt = select(Container).where(Container.user_id == user.id).order_by(Container.name)
        if container_type is not None:
            stmt = stmt.where(Container.type == container_type)
        result = await db.execute(stmt)
        return [_container_dict(c) for c in result.scalars().all()]


@mcp_server.tool()
async def get_container(container_id: int) -> dict:
    """Get a container's detail, including any square support structures (trellis/cage/pole)."""
    async with async_session() as db:
        user = await get_mcp_user(db)
        stmt = (
            select(Container)
            .options(selectinload(Container.square_supports))
            .where(Container.id == container_id, Container.user_id == user.id)
        )
        result = await db.execute(stmt)
        container = result.scalar_one_or_none()
        if not container:
            raise ToolError(f"Container {container_id} not found")

        data = _container_dict(container)
        data["square_supports"] = [
            {"square_x": s.square_x, "square_y": s.square_y, "support_type": s.support_type}
            for s in container.square_supports
        ]
        return data


@mcp_server.tool()
async def list_yards() -> list[dict]:
    """List the user's yards (named spatial layouts of beds and features)."""
    async with async_session() as db:
        user = await get_mcp_user(db)
        stmt = select(Yard).where(Yard.user_id == user.id).order_by(Yard.name)
        result = await db.execute(stmt)
        return [{"id": y.id, "name": y.name, "width": y.width, "height": y.height} for y in result.scalars().all()]


@mcp_server.tool()
async def get_yard(yard_id: int) -> dict:
    """Get a yard's detail, including every placed bed/feature object."""
    async with async_session() as db:
        user = await get_mcp_user(db)
        stmt = (
            select(Yard)
            .options(selectinload(Yard.objects).selectinload(YardObject.container))
            .where(Yard.id == yard_id, Yard.user_id == user.id)
        )
        result = await db.execute(stmt)
        yard = result.scalar_one_or_none()
        if not yard:
            raise ToolError(f"Yard {yard_id} not found")

        objects = []
        for o in yard.objects:
            width = o.square_width or (o.container.width if o.container else 1)
            height = o.square_height or (o.container.height if o.container else 1)
            objects.append(
                {
                    "id": o.id,
                    "object_type": o.object_type,
                    "container_id": o.container_id,
                    "container_name": o.container.name if o.container else None,
                    "label": o.label,
                    "square_x": o.square_x,
                    "square_y": o.square_y,
                    "square_width": width,
                    "square_height": height,
                }
            )
        return {"id": yard.id, "name": yard.name, "width": yard.width, "height": yard.height, "objects": objects}


def _planting_dict(p: Planting) -> dict:
    lifecycle = None
    if p.variety:
        phase = compute_lifecycle_phase(
            status=p.status,
            start_date=p.start_date,
            end_date=p.end_date,
            days_to_germination_min=p.variety.days_to_germination_min,
            days_to_germination_max=p.variety.days_to_germination_max,
            days_to_harvest_min=p.variety.days_to_harvest_min,
            days_to_harvest_max=p.variety.days_to_harvest_max,
            seed_start_date=p.seed_start_date,
        )
        lifecycle = {
            "phase": phase.phase,
            "phase_display": phase.phase_display,
            "progress_percent": phase.progress_percent,
        }

    return {
        "id": p.id,
        "container_id": p.container_id,
        "container_name": p.container.name if p.container else None,
        "variety_id": p.variety_id,
        "variety_name": p.variety.name if p.variety else None,
        "square_x": p.square_x,
        "square_y": p.square_y,
        "square_width": p.square_width,
        "square_height": p.square_height,
        "tower_level": p.tower_level,
        "start_date": _iso(p.start_date),
        "end_date": _iso(p.end_date),
        "seed_start_date": _iso(p.seed_start_date),
        "status": p.status,
        "planting_method": p.planting_method,
        "quantity": p.quantity,
        "removal_reason": p.removal_reason,
        "start_id": p.start_id,
        "lifecycle": lifecycle,
    }


@mcp_server.tool()
async def list_plantings(
    container_id: int | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = DEFAULT_LIST_LIMIT,
) -> list[dict]:
    """List plantings, optionally filtered by container, status (not_started/in_progress/complete),
    or a date range (plantings overlapping [start_date, end_date] are returned).
    Defaults to the 100 most recent — pass filters to narrow down large gardens."""
    async with async_session() as db:
        user = await get_mcp_user(db)
        stmt = (
            select(Planting)
            .options(selectinload(Planting.variety), selectinload(Planting.container))
            .where(Planting.user_id == user.id)
            .order_by(Planting.start_date.desc())
            .limit(limit)
        )
        if container_id is not None:
            stmt = stmt.where(Planting.container_id == container_id)
        if status is not None:
            stmt = stmt.where(Planting.status == status)
        if start_date is not None:
            stmt = stmt.where(Planting.end_date >= start_date)
        if end_date is not None:
            stmt = stmt.where(Planting.start_date <= end_date)

        result = await db.execute(stmt)
        return [_planting_dict(p) for p in result.scalars().all()]


@mcp_server.tool()
async def get_planting(planting_id: int) -> dict:
    """Get a single planting's detail, including its computed lifecycle phase."""
    async with async_session() as db:
        user = await get_mcp_user(db)
        stmt = (
            select(Planting)
            .options(selectinload(Planting.variety), selectinload(Planting.container))
            .where(Planting.id == planting_id, Planting.user_id == user.id)
        )
        result = await db.execute(stmt)
        planting = result.scalar_one_or_none()
        if not planting:
            raise ToolError(f"Planting {planting_id} not found")
        return _planting_dict(planting)


@mcp_server.tool()
async def list_tasks(
    status: str | None = None,
    source: str | None = None,
    category: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    include_undated: bool = True,
    limit: int = DEFAULT_LIST_LIMIT,
) -> list[dict]:
    """List tasks, optionally filtered by status (pending/completed/dismissed), source (auto/manual),
    category (watering/harvest/planting/seed_starting/pest_disease/maintenance/general), or due-date
    range. Each task's remind_at (if set) is returned in the app's local timezone.

    Tasks with no due date are still returned when a date range is given (they're "do whenever"
    items that belong in a "what do I need to do today/this week" answer) — pass
    include_undated=False to get only tasks actually due in the range."""
    async with async_session() as db:
        user = await get_mcp_user(db)
        stmt = (
            select(Task)
            .options(selectinload(Task.container), selectinload(Task.variety))
            .where(Task.user_id == user.id)
            .order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if source is not None:
            stmt = stmt.where(Task.source == source)
        if category is not None:
            stmt = stmt.where(Task.category == category)
        date_conds = []
        if start_date is not None:
            date_conds.append(Task.due_date >= start_date)
        if end_date is not None:
            date_conds.append(Task.due_date <= end_date)
        if date_conds:
            in_range = and_(*date_conds)
            stmt = stmt.where(or_(in_range, Task.due_date.is_(None)) if include_undated else in_range)

        result = await db.execute(stmt)
        return [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "due_date": _iso(t.due_date),
                "source": t.source,
                "status": t.status,
                "category": t.category,
                "remind_at": _local_iso(t.remind_at),
                "reminder_sent": t.reminder_sent,
                "container_id": t.container_id,
                "planting_id": t.planting_id,
                "variety_id": t.variety_id,
                "container_name": t.container.name if t.container else None,
                "variety_name": t.variety.name if t.variety else None,
            }
            for t in result.scalars().all()
        ]


@mcp_server.tool()
async def get_recommendations(
    container_id: int,
    square_x: int,
    square_y: int,
    target_date: date | None = None,
) -> dict:
    """'What can I plant here?' — recommend varieties for a specific square on a given date
    (defaults to today), scored by season fit, size fit, harvest-deadline fit, companion
    planting, and support-structure match."""
    async with async_session() as db:
        user = await get_mcp_user(db)
        check_date = target_date or date.today()
        results = await _get_recommendations(
            db=db,
            user_id=user.id,
            container_id=container_id,
            square_x=square_x,
            square_y=square_y,
            target_date=check_date,
        )
        return {
            "date": _iso(check_date),
            "container_id": container_id,
            "square_x": square_x,
            "square_y": square_y,
            "recommendations": [
                {
                    "variety_id": r.variety_id,
                    "variety_name": r.variety_name,
                    "category_name": r.category_name,
                    "score": round(r.score, 1),
                    "days_to_harvest_min": r.days_to_harvest_min,
                    "days_to_harvest_max": r.days_to_harvest_max,
                    "planting_method": r.planting_method,
                    "is_climbing": r.is_climbing,
                    "spacing": r.spacing,
                    "warnings": r.warnings,
                    "boosts": r.boosts,
                }
                for r in results
            ],
        }
