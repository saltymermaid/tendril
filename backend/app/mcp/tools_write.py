"""Narrow write MCP tools — create/update varieties and categories, create a planting,
complete a planting, create/edit a task, change a task's status, create a plant start. Still
no deletes and no container/yard/plant-start mutations beyond creation, by design (see
the plan's confirmed v1 write scope) — variety and category writes were added on top of
that scope so the catalog can be maintained from an MCP client.

Validation is reused, not duplicated: `_check_overlap` and `validate_planting_bounds`
are imported directly from the REST plantings router so the two entry points can't
drift. Both raise `HTTPException` (a plain exception class, safe to raise outside a
route handler) — caught here and re-raised as `ToolError` so the message reaches the
MCP client (a plain `ValueError` would be masked by the SDK into a generic
"Error executing tool X" with no detail — see mcp/server/mcpserver/tools/base.py).
"""

from datetime import date, datetime

from fastapi import HTTPException
from mcp.server.mcpserver.exceptions import ToolError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.mcp.server import mcp_server
from app.mcp.context import get_mcp_user
from app.models.category import Category, PlantingSeason
from app.models.container import Container
from app.models.plant_start import PlantStart
from app.models.planting import Planting
from app.models.task import TASK_CATEGORIES, Task
from app.models.variety import Variety
from app.mcp.tools_read import (
    _category_dict,
    _get_category_detail,
    _local_iso,
    _planting_dict,
    _plant_start_dict,
    _variety_dict,
)
from app.routers.plantings import _check_overlap, _consume_plant_start, validate_planting_bounds
from app.services.localtime import to_utc

VALID_REMOVAL_REASONS = {"harvest_complete", "died", "pulled_early", "pest_disease", "other"}
VALID_PLANTING_METHODS = {"direct_sow", "transplant", "both"}
VALID_HARVEST_TYPES = {"single", "continuous"}
VALID_TASK_STATUSES = {"pending", "completed", "dismissed"}


def _planting_season_from_dict(category_id: int, ps: dict) -> PlantingSeason:
    try:
        return PlantingSeason(
            category_id=category_id,
            usda_zone=ps["usda_zone"],
            start_month=ps["start_month"],
            start_day=ps["start_day"],
            end_month=ps["end_month"],
            end_day=ps["end_day"],
        )
    except KeyError as exc:
        raise ToolError(
            f"planting_seasons entry missing required field {exc}. Each entry needs "
            "usda_zone, start_month, start_day, end_month, end_day."
        ) from exc


@mcp_server.tool()
async def create_variety(
    name: str,
    category_id: int,
    days_to_germination_min: int | None = None,
    days_to_germination_max: int | None = None,
    days_to_harvest_min: int | None = None,
    days_to_harvest_max: int | None = None,
    seed_start_days: int | None = None,
    planting_depth: str | None = None,
    spacing: str = "1x1",
    sunlight: str | None = None,
    is_climbing: bool = False,
    planting_method: str = "both",
    source_url: str | None = None,
    notes: str | None = None,
) -> dict:
    """Add a new plant variety to the catalog under an existing category (see
    list_categories for category_id). days_to_harvest is measured from seed, not from
    transplant. planting_method must be one of: direct_sow, transplant, both."""
    if planting_method not in VALID_PLANTING_METHODS:
        raise ToolError(f"planting_method must be one of: {', '.join(sorted(VALID_PLANTING_METHODS))}")

    async with async_session() as db:
        user = await get_mcp_user(db)

        result = await db.execute(select(Category).where(Category.id == category_id))
        if not result.scalar_one_or_none():
            raise ToolError(f"Category {category_id} not found")

        variety = Variety(
            user_id=user.id,
            category_id=category_id,
            name=name,
            days_to_germination_min=days_to_germination_min,
            days_to_germination_max=days_to_germination_max,
            days_to_harvest_min=days_to_harvest_min,
            days_to_harvest_max=days_to_harvest_max,
            seed_start_days=seed_start_days,
            planting_depth=planting_depth,
            spacing=spacing,
            sunlight=sunlight,
            is_climbing=is_climbing,
            planting_method=planting_method,
            source_url=source_url,
            notes=notes,
        )
        db.add(variety)
        await db.commit()
        await db.refresh(variety)

        result = await db.execute(
            select(Variety).options(selectinload(Variety.category)).where(Variety.id == variety.id)
        )
        return _variety_dict(result.scalar_one())


@mcp_server.tool()
async def update_variety(
    variety_id: int,
    name: str | None = None,
    category_id: int | None = None,
    days_to_germination_min: int | None = None,
    days_to_germination_max: int | None = None,
    days_to_harvest_min: int | None = None,
    days_to_harvest_max: int | None = None,
    seed_start_days: int | None = None,
    planting_depth: str | None = None,
    spacing: str | None = None,
    sunlight: str | None = None,
    is_climbing: bool | None = None,
    planting_method: str | None = None,
    source_url: str | None = None,
    notes: str | None = None,
) -> dict:
    """Update a variety's fields — only the ones you pass are changed. planting_method,
    if given, must be one of: direct_sow, transplant, both. Note: passing a field with
    value None leaves it unchanged rather than clearing it (no way to blank out an
    already-set field through this tool)."""
    if planting_method is not None and planting_method not in VALID_PLANTING_METHODS:
        raise ToolError(f"planting_method must be one of: {', '.join(sorted(VALID_PLANTING_METHODS))}")

    async with async_session() as db:
        user = await get_mcp_user(db)

        result = await db.execute(select(Variety).where(Variety.id == variety_id, Variety.user_id == user.id))
        variety = result.scalar_one_or_none()
        if not variety:
            raise ToolError(f"Variety {variety_id} not found")

        if category_id is not None and category_id != variety.category_id:
            cat_result = await db.execute(select(Category).where(Category.id == category_id))
            if not cat_result.scalar_one_or_none():
                raise ToolError(f"Category {category_id} not found")

        updates = {
            "name": name,
            "category_id": category_id,
            "days_to_germination_min": days_to_germination_min,
            "days_to_germination_max": days_to_germination_max,
            "days_to_harvest_min": days_to_harvest_min,
            "days_to_harvest_max": days_to_harvest_max,
            "seed_start_days": seed_start_days,
            "planting_depth": planting_depth,
            "spacing": spacing,
            "sunlight": sunlight,
            "is_climbing": is_climbing,
            "planting_method": planting_method,
            "source_url": source_url,
            "notes": notes,
        }
        for field, value in updates.items():
            if value is not None:
                setattr(variety, field, value)

        await db.commit()

        result = await db.execute(
            select(Variety).options(selectinload(Variety.category)).where(Variety.id == variety_id)
        )
        return _variety_dict(result.scalar_one())


@mcp_server.tool()
async def create_planting(
    container_id: int,
    variety_id: int,
    square_x: int,
    square_y: int,
    start_date: date,
    end_date: date,
    square_width: int = 1,
    square_height: int = 1,
    tower_level: int | None = None,
    planting_method: str | None = None,
    quantity: int | None = None,
    start_id: int | None = None,
) -> dict:
    """Create a new planting — assign a variety to a square (or squares) of a container
    for a date range. Rejects overlaps with existing plantings on the same squares/dates
    and positions outside the container's bounds. If start_id is given, decrements that
    many (quantity, default 1) from the referenced plant start — it must be for the same
    variety and have enough remaining."""
    async with async_session() as db:
        user = await get_mcp_user(db)

        result = await db.execute(
            select(Container).where(Container.id == container_id, Container.user_id == user.id)
        )
        container = result.scalar_one_or_none()
        if not container:
            raise ToolError(f"Container {container_id} not found")

        result = await db.execute(select(Variety).where(Variety.id == variety_id, Variety.user_id == user.id))
        variety = result.scalar_one_or_none()
        if not variety:
            raise ToolError(f"Variety {variety_id} not found")

        if end_date <= start_date:
            raise ToolError("end_date must be after start_date")

        try:
            validate_planting_bounds(
                container=container,
                square_x=square_x,
                square_y=square_y,
                square_width=square_width,
                square_height=square_height,
                tower_level=tower_level,
            )
            await _check_overlap(
                db=db,
                user_id=user.id,
                container_id=container_id,
                square_x=square_x,
                square_y=square_y,
                square_width=square_width,
                square_height=square_height,
                start_date=start_date,
                end_date=end_date,
            )
            if start_id is not None:
                await _consume_plant_start(
                    db=db,
                    user_id=user.id,
                    start_id=start_id,
                    variety_id=variety_id,
                    quantity=quantity or 1,
                )
        except HTTPException as exc:
            raise ToolError(exc.detail) from exc

        planting = Planting(
            user_id=user.id,
            container_id=container_id,
            variety_id=variety_id,
            square_x=square_x,
            square_y=square_y,
            square_width=square_width,
            square_height=square_height,
            tower_level=tower_level,
            start_date=start_date,
            end_date=end_date,
            planting_method=planting_method,
            quantity=quantity,
            start_id=start_id,
            status="not_started",
        )
        db.add(planting)
        await db.commit()
        await db.refresh(planting)

        result = await db.execute(
            select(Planting)
            .options(selectinload(Planting.variety), selectinload(Planting.container))
            .where(Planting.id == planting.id)
        )
        loaded = result.scalar_one()
        return _planting_dict(loaded)


@mcp_server.tool()
async def complete_planting(
    planting_id: int,
    removal_reason: str,
    actual_end_date: date | None = None,
) -> dict:
    """Transition a planting from in_progress to complete. removal_reason must be one of:
    harvest_complete, died, pulled_early, pest_disease, other. actual_end_date defaults to today."""
    async with async_session() as db:
        user = await get_mcp_user(db)

        result = await db.execute(select(Planting).where(Planting.id == planting_id, Planting.user_id == user.id))
        planting = result.scalar_one_or_none()
        if not planting:
            raise ToolError(f"Planting {planting_id} not found")

        if planting.status != "in_progress":
            raise ToolError(
                f"Cannot complete planting with status '{planting.status}'. "
                "Only 'in_progress' plantings can be completed."
            )
        if removal_reason not in VALID_REMOVAL_REASONS:
            raise ToolError(f"Invalid removal_reason. Must be one of: {', '.join(sorted(VALID_REMOVAL_REASONS))}")

        actual_end = actual_end_date or date.today()
        if actual_end < planting.start_date:
            raise ToolError("actual_end_date must be on or after start_date")

        planting.end_date = actual_end
        planting.status = "complete"
        planting.removal_reason = removal_reason
        await db.commit()

        result = await db.execute(
            select(Planting)
            .options(selectinload(Planting.variety), selectinload(Planting.container))
            .where(Planting.id == planting.id)
        )
        loaded = result.scalar_one()
        return _planting_dict(loaded)


@mcp_server.tool()
async def create_plant_start(variety_id: int, start_date: date, quantity: int = 1) -> dict:
    """Record a new plant start — a batch of seedlings started (e.g. in trays), not yet
    assigned to a bed. Pick these up later via start_id when calling create_planting."""
    async with async_session() as db:
        user = await get_mcp_user(db)

        result = await db.execute(select(Variety).where(Variety.id == variety_id, Variety.user_id == user.id))
        if not result.scalar_one_or_none():
            raise ToolError(f"Variety {variety_id} not found")

        start = PlantStart(user_id=user.id, variety_id=variety_id, start_date=start_date, quantity=quantity)
        db.add(start)
        await db.commit()

        result = await db.execute(
            select(PlantStart).options(selectinload(PlantStart.variety)).where(PlantStart.id == start.id)
        )
        return _plant_start_dict(result.scalar_one())


def _task_dict(t: Task) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "source": t.source,
        "status": t.status,
        "category": t.category,
        "remind_at": _local_iso(t.remind_at),
        "reminder_sent": t.reminder_sent,
        "container_id": t.container_id,
        "planting_id": t.planting_id,
        "variety_id": t.variety_id,
    }


@mcp_server.tool()
async def create_task(
    title: str,
    description: str | None = None,
    due_date: date | None = None,
    category: str = "general",
    remind_at: datetime | None = None,
    container_id: int | None = None,
    planting_id: int | None = None,
    variety_id: int | None = None,
) -> dict:
    """Create a manual task (source is always 'manual' — auto tasks come from the task generator).

    category must be one of: watering, harvest, planting, seed_starting, pest_disease,
    maintenance, general.

    remind_at, if given, schedules a push notification: pass it as local time
    (America/New_York, where the garden is) with no timezone offset, e.g.
    "2026-09-27T18:00:00" for 6pm tomorrow — it's interpreted as local time automatically.
    """
    if category not in TASK_CATEGORIES:
        raise ToolError(f"category must be one of: {', '.join(sorted(TASK_CATEGORIES))}")

    async with async_session() as db:
        user = await get_mcp_user(db)
        task = Task(
            user_id=user.id,
            title=title,
            description=description,
            due_date=due_date,
            source="manual",
            category=category,
            remind_at=to_utc(remind_at),
            container_id=container_id,
            planting_id=planting_id,
            variety_id=variety_id,
        )
        db.add(task)
        await db.commit()
        return _task_dict(task)


@mcp_server.tool()
async def update_task_status(task_id: int, status: str) -> dict:
    """Change a task's status. status must be one of: pending, completed, dismissed
    (pending re-opens a completed/dismissed task)."""
    if status not in VALID_TASK_STATUSES:
        raise ToolError(f"status must be one of: {', '.join(sorted(VALID_TASK_STATUSES))}")

    async with async_session() as db:
        user = await get_mcp_user(db)
        result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
        task = result.scalar_one_or_none()
        if not task:
            raise ToolError(f"Task {task_id} not found")

        task.status = status
        await db.commit()
        return {"id": task.id, "title": task.title, "status": task.status}


@mcp_server.tool()
async def update_task(
    task_id: int,
    title: str | None = None,
    description: str | None = None,
    due_date: date | None = None,
    category: str | None = None,
    remind_at: datetime | None = None,
) -> dict:
    """Edit an existing task's title, description, due date, category, or reminder time.
    Only the fields you pass are changed. Rescheduling remind_at lets it fire again even
    if the previous reminder already went out. To change status, use update_task_status."""
    if category is not None and category not in TASK_CATEGORIES:
        raise ToolError(f"category must be one of: {', '.join(sorted(TASK_CATEGORIES))}")

    async with async_session() as db:
        user = await get_mcp_user(db)
        result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
        task = result.scalar_one_or_none()
        if not task:
            raise ToolError(f"Task {task_id} not found")

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if due_date is not None:
            task.due_date = due_date
        if category is not None:
            task.category = category
        if remind_at is not None:
            task.remind_at = to_utc(remind_at)
            task.reminder_sent = False

        await db.commit()
        return _task_dict(task)


@mcp_server.tool()
async def create_category(
    name: str,
    color: str,
    harvest_type: str = "continuous",
    icon_svg: str | None = None,
    planting_seasons: list[dict] | None = None,
) -> dict:
    """Add a new plant category to the catalog (global — shared across every user of this
    Tendril instance, like Tomatoes or Peppers). color is a hex string like '#FF5733'.
    harvest_type must be 'single' (one harvest ends the planting, e.g. a head of lettuce)
    or 'continuous' (repeated harvests over time, e.g. tomatoes). Each planting_seasons
    entry needs usda_zone, start_month, start_day, end_month, end_day — this garden is
    Zone 10a."""
    if harvest_type not in VALID_HARVEST_TYPES:
        raise ToolError(f"harvest_type must be one of: {', '.join(sorted(VALID_HARVEST_TYPES))}")

    async with async_session() as db:
        await get_mcp_user(db)

        existing = await db.execute(select(Category).where(Category.name == name))
        if existing.scalar_one_or_none():
            raise ToolError(f"Category '{name}' already exists")

        category = Category(name=name, color=color, harvest_type=harvest_type, icon_svg=icon_svg)
        db.add(category)
        await db.flush()

        for ps in planting_seasons or []:
            db.add(_planting_season_from_dict(category.id, ps))

        await db.commit()

        loaded = await _get_category_detail(db, category.id)
        return _category_dict(loaded)


@mcp_server.tool()
async def update_category(
    category_id: int,
    name: str | None = None,
    color: str | None = None,
    harvest_type: str | None = None,
    icon_svg: str | None = None,
    planting_seasons: list[dict] | None = None,
) -> dict:
    """Update a category's fields — only the ones you pass are changed. Passing
    planting_seasons replaces the category's entire season list (each entry needs
    usda_zone, start_month, start_day, end_month, end_day)."""
    if harvest_type is not None and harvest_type not in VALID_HARVEST_TYPES:
        raise ToolError(f"harvest_type must be one of: {', '.join(sorted(VALID_HARVEST_TYPES))}")

    async with async_session() as db:
        await get_mcp_user(db)

        result = await db.execute(
            select(Category).options(selectinload(Category.planting_seasons)).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()
        if not category:
            raise ToolError(f"Category {category_id} not found")

        if name is not None and name != category.name:
            dup = await db.execute(select(Category).where(Category.name == name, Category.id != category_id))
            if dup.scalar_one_or_none():
                raise ToolError(f"Category '{name}' already exists")
            category.name = name
        if color is not None:
            category.color = color
        if harvest_type is not None:
            category.harvest_type = harvest_type
        if icon_svg is not None:
            category.icon_svg = icon_svg

        if planting_seasons is not None:
            for ps in category.planting_seasons:
                await db.delete(ps)
            for ps in planting_seasons:
                db.add(_planting_season_from_dict(category.id, ps))

        await db.commit()

        loaded = await _get_category_detail(db, category_id)
        return _category_dict(loaded)
