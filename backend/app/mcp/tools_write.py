"""Narrow write MCP tools — create/update varieties and categories, create/edit/delete a
planting, complete a planting, create/edit a task, change a task's status, create/edit/delete a
plant start, edit a container's name/location/irrigation. update_planting and delete_planting are
both restricted to not_started plantings — editing or removing something already in the ground
stays REST/UI-only (see complete_planting for recording an actual removal). No yard mutations, and
no container resize/create/delete, by design (see the plan's confirmed v1 write scope) — variety,
category, plant-start, and container-detail writes were added on top of that scope so the garden
can be maintained from an MCP client.

end_date must be computed from seed_start_date (or the referenced plant start's start_date)
when transplanting, not from start_date — days_to_harvest on Variety is measured from seed,
and start_date here means "went into this square," which for a transplant is well after the
seed was actually started. Get the variety's days_to_harvest and, if transplanting, the plant
start's start_date (via get_variety / list_plant_starts) before calling create_planting.

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
    _container_dict,
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
VALID_HARVEST_TYPES = {"single", "continuous", "none"}
VALID_TASK_STATUSES = {"pending", "completed", "dismissed"}
# Same options the container form offers (frontend/src/pages/ContainerFormPage.tsx).
VALID_IRRIGATION_TYPES = {"drip", "manual", "sprinkler"}
VALID_IRRIGATION_FREQUENCIES = {"daily", "2x_daily", "every_2_days", "every_3_days", "weekly"}


def _validate_harvest_fields(
    harvest_type_override: str | None, plants_per_square: int | None, allow_clear: bool = False
) -> None:
    """allow_clear: update tools accept plants_per_square=0 as "clear it"."""
    if harvest_type_override is not None and harvest_type_override not in VALID_HARVEST_TYPES:
        raise ToolError(f"harvest_type_override must be one of: {', '.join(sorted(VALID_HARVEST_TYPES))}")
    if plants_per_square is not None and plants_per_square < (0 if allow_clear else 1):
        raise ToolError("plants_per_square must be at least 1")


def _apply_harvest_count_fields(obj, harvest_unit: str | None, plants_per_square: int | None) -> None:
    """Set harvest_unit / plants_per_square on a Variety or Category for an update tool:
    None leaves the field alone, "" / 0 clears it."""
    if harvest_unit is not None:
        obj.harvest_unit = harvest_unit.strip() or None
    if plants_per_square is not None:
        obj.plants_per_square = plants_per_square or None


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
    harvest_type_override: str | None = None,
    harvest_unit: str | None = None,
    plants_per_square: int | None = None,
    source_url: str | None = None,
    notes: str | None = None,
) -> dict:
    """Add a new plant variety to the catalog under an existing category (see
    list_categories for category_id). days_to_harvest is measured from seed, not from
    transplant. planting_method must be one of: direct_sow, transplant, both.

    Harvest forecast fields all override the category's value for just this variety, and are
    best left unset so it inherits the category's (see list_categories): harvest_type_override
    (single/continuous/none) — e.g. head lettuce 'single' under a 'continuous' Lettuce category,
    or a marigold 'none' so it's left out of the forecast. harvest_unit is a singular noun for one
    plant's harvest (head, bunch, root). plants_per_square is how many plants fill one planting's
    footprint (16 radishes in a 1x1, 1 tomato in a 2x2) — set it only when this variety differs
    from its category (e.g. pole beans at 8 when Beans is 9)."""
    _validate_harvest_fields(harvest_type_override, plants_per_square)
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
            harvest_type_override=harvest_type_override,
            harvest_unit=harvest_unit,
            plants_per_square=plants_per_square,
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
    harvest_type_override: str | None = None,
    harvest_unit: str | None = None,
    plants_per_square: int | None = None,
    source_url: str | None = None,
    notes: str | None = None,
) -> dict:
    """Update a variety's fields — only the ones you pass are changed. planting_method,
    if given, must be one of: direct_sow, transplant, both.

    The harvest fields override the category's values; to go back to inheriting the category's,
    pass harvest_type_override='category', harvest_unit='', or plants_per_square=0. Prefer
    setting a default on the category (update_category) over setting the same value on each of
    its varieties. Note: other fields passed as None are left unchanged rather than cleared."""
    clear_harvest_override = harvest_type_override == "category"
    if clear_harvest_override:
        harvest_type_override = None
    _validate_harvest_fields(harvest_type_override, plants_per_square, allow_clear=True)
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
            "harvest_type_override": harvest_type_override,
            "source_url": source_url,
            "notes": notes,
        }
        for field, value in updates.items():
            if value is not None:
                setattr(variety, field, value)
        if clear_harvest_override:
            variety.harvest_type_override = None
        _apply_harvest_count_fields(variety, harvest_unit, plants_per_square)

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
    seed_start_date: date | None = None,
) -> dict:
    """Create a new planting — assign a variety to a square (or squares) of a container
    for a date range. Rejects overlaps with existing plantings on the same squares/dates
    and positions outside the container's bounds. If start_id is given, decrements that
    many (quantity, default 1) from the referenced plant start — it must be for the same
    variety and have enough remaining, and seed_start_date defaults to that start's
    start_date if not given. seed_start_date (defaulted or explicit) is what
    days_to_harvest is measured from — see the module docstring; start_date is just when
    it went into this square."""
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

        if seed_start_date and seed_start_date > start_date:
            raise ToolError("seed_start_date must be on or before start_date")

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
                consumed_start = await _consume_plant_start(
                    db=db,
                    user_id=user.id,
                    start_id=start_id,
                    variety_id=variety_id,
                    quantity=quantity or 1,
                )
                if seed_start_date is None:
                    seed_start_date = consumed_start.start_date
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
            seed_start_date=seed_start_date,
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
async def update_planting(
    planting_id: int,
    square_x: int | None = None,
    square_y: int | None = None,
    variety_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    seed_start_date: date | None = None,
    planting_method: str | None = None,
    quantity: int | None = None,
) -> dict:
    """Edit a planned (not_started) planting — move it to a different square, swap its
    variety, or adjust its dates/method/quantity. Only works while status is not_started
    (this is for previewing/adjusting a plan before anything is in the ground); once a
    planting is in_progress or complete, edit it in the app instead. Re-checks bounds and
    overlap if position or dates change."""
    async with async_session() as db:
        user = await get_mcp_user(db)

        result = await db.execute(
            select(Planting)
            .options(selectinload(Planting.container))
            .where(Planting.id == planting_id, Planting.user_id == user.id)
        )
        planting = result.scalar_one_or_none()
        if not planting:
            raise ToolError(f"Planting {planting_id} not found")
        if planting.status != "not_started":
            raise ToolError(
                f"Cannot edit planting with status '{planting.status}' via chat. "
                "Only 'not_started' plantings can be edited this way."
            )

        if variety_id is not None:
            result = await db.execute(select(Variety).where(Variety.id == variety_id, Variety.user_id == user.id))
            if not result.scalar_one_or_none():
                raise ToolError(f"Variety {variety_id} not found")

        new_x = square_x if square_x is not None else planting.square_x
        new_y = square_y if square_y is not None else planting.square_y
        new_start = start_date or planting.start_date
        new_end = end_date or planting.end_date
        new_seed_start = seed_start_date if seed_start_date is not None else planting.seed_start_date

        if new_end <= new_start:
            raise ToolError("end_date must be after start_date")
        if new_seed_start and new_seed_start > new_start:
            raise ToolError("seed_start_date must be on or before start_date")

        try:
            validate_planting_bounds(
                container=planting.container,
                square_x=new_x,
                square_y=new_y,
                square_width=planting.square_width,
                square_height=planting.square_height,
                tower_level=planting.tower_level,
            )
            await _check_overlap(
                db=db,
                user_id=user.id,
                container_id=planting.container_id,
                square_x=new_x,
                square_y=new_y,
                square_width=planting.square_width,
                square_height=planting.square_height,
                start_date=new_start,
                end_date=new_end,
                exclude_planting_id=planting.id,
            )
        except HTTPException as exc:
            raise ToolError(exc.detail) from exc

        planting.square_x = new_x
        planting.square_y = new_y
        if variety_id is not None:
            planting.variety_id = variety_id
        planting.start_date = new_start
        planting.end_date = new_end
        planting.seed_start_date = new_seed_start
        if planting_method is not None:
            planting.planting_method = planting_method
        if quantity is not None:
            planting.quantity = quantity

        await db.commit()

        result = await db.execute(
            select(Planting)
            .options(selectinload(Planting.variety), selectinload(Planting.container))
            .where(Planting.id == planting.id)
        )
        loaded = result.scalar_one()
        return _planting_dict(loaded)


@mcp_server.tool()
async def delete_planting(planting_id: int) -> dict:
    """Delete a planned (not_started) planting outright — for backing out a plan you don't
    want, e.g. "don't put the broccoli there." Only works while status is not_started; a
    planting already in the ground or complete can't be deleted this way (removes its
    history) — use complete_planting to record it ending, or edit it in the app. If it was
    transplanted from a plant start, that start's quantity is restored."""
    async with async_session() as db:
        user = await get_mcp_user(db)

        result = await db.execute(select(Planting).where(Planting.id == planting_id, Planting.user_id == user.id))
        planting = result.scalar_one_or_none()
        if not planting:
            raise ToolError(f"Planting {planting_id} not found")
        if planting.status != "not_started":
            raise ToolError(
                f"Cannot delete planting with status '{planting.status}'. "
                "Only 'not_started' plantings can be deleted this way."
            )

        if planting.start_id is not None:
            result = await db.execute(
                select(PlantStart).where(PlantStart.id == planting.start_id, PlantStart.user_id == user.id)
            )
            start = result.scalar_one_or_none()
            if start:
                start.quantity += planting.quantity or 1

        await db.delete(planting)
        await db.commit()
        return {"deleted": True, "planting_id": planting_id}


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


@mcp_server.tool()
async def update_plant_start(
    start_id: int,
    variety_id: int | None = None,
    start_date: date | None = None,
    quantity: int | None = None,
) -> dict:
    """Edit a plant start's variety, start date, or remaining quantity — only the fields you
    pass are changed. quantity is what's left in the tray (not yet planted), so set it to 0 if
    the rest died or were given away. Plantings already transplanted from this start keep their
    own seed_start_date; changing start_date here doesn't rewrite them (use update_planting)."""
    if quantity is not None and quantity < 0:
        raise ToolError("quantity cannot be negative")

    async with async_session() as db:
        user = await get_mcp_user(db)

        result = await db.execute(
            select(PlantStart).where(PlantStart.id == start_id, PlantStart.user_id == user.id)
        )
        start = result.scalar_one_or_none()
        if not start:
            raise ToolError(f"Plant start {start_id} not found")

        if variety_id is not None and variety_id != start.variety_id:
            result = await db.execute(select(Variety).where(Variety.id == variety_id, Variety.user_id == user.id))
            if not result.scalar_one_or_none():
                raise ToolError(f"Variety {variety_id} not found")
            start.variety_id = variety_id
        if start_date is not None:
            start.start_date = start_date
        if quantity is not None:
            start.quantity = quantity

        await db.commit()

        result = await db.execute(
            select(PlantStart).options(selectinload(PlantStart.variety)).where(PlantStart.id == start_id)
        )
        return _plant_start_dict(result.scalar_one())


@mcp_server.tool()
async def delete_plant_start(start_id: int) -> dict:
    """Delete a plant start outright — for a batch entered by mistake or one that failed
    entirely. Plantings already transplanted from it are kept (they just lose the link back to
    this start; their seed_start_date is unaffected). To record that some seedlings are gone but
    keep the rest, use update_plant_start to lower quantity instead."""
    async with async_session() as db:
        user = await get_mcp_user(db)

        result = await db.execute(
            select(PlantStart).where(PlantStart.id == start_id, PlantStart.user_id == user.id)
        )
        start = result.scalar_one_or_none()
        if not start:
            raise ToolError(f"Plant start {start_id} not found")

        await db.delete(start)
        await db.commit()
        return {"deleted": True, "start_id": start_id}


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


async def _resolve_task_links(
    db, user, container_id: int | None, planting_id: int | None, variety_id: int | None
) -> tuple[int | None, int | None, int | None]:
    """Check that each given link belongs to the user, and fill in container_id/variety_id from
    the planting when only planting_id is given (so "harvest the roselle in Bed 5" links all
    three). Returns the (container_id, planting_id, variety_id) to store; 0 passes through as-is
    for update_task's "clear this link" meaning."""
    if planting_id:
        result = await db.execute(
            select(Planting).where(Planting.id == planting_id, Planting.user_id == user.id)
        )
        planting = result.scalar_one_or_none()
        if not planting:
            raise ToolError(f"Planting {planting_id} not found")
        if container_id is None:
            container_id = planting.container_id
        if variety_id is None:
            variety_id = planting.variety_id
    if container_id:
        result = await db.execute(
            select(Container.id).where(Container.id == container_id, Container.user_id == user.id)
        )
        if result.scalar_one_or_none() is None:
            raise ToolError(f"Container {container_id} not found")
    if variety_id:
        result = await db.execute(
            select(Variety.id).where(Variety.id == variety_id, Variety.user_id == user.id)
        )
        if result.scalar_one_or_none() is None:
            raise ToolError(f"Variety {variety_id} not found")
    return container_id, planting_id, variety_id


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

    Link the task to what it's about: container_id for a bed or the tower (see list_containers),
    planting_id for a specific planting — passing only planting_id also fills in its container
    and variety.
    """
    if category not in TASK_CATEGORIES:
        raise ToolError(f"category must be one of: {', '.join(sorted(TASK_CATEGORIES))}")

    async with async_session() as db:
        user = await get_mcp_user(db)
        container_id, planting_id, variety_id = await _resolve_task_links(
            db, user, container_id, planting_id, variety_id
        )
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
    container_id: int | None = None,
    planting_id: int | None = None,
    variety_id: int | None = None,
) -> dict:
    """Edit an existing task's title, description, due date, category, reminder time, or what
    it's linked to (container_id / planting_id / variety_id). Only the fields you pass are
    changed. Passing only planting_id also re-links the task to that planting's container and
    variety. Pass 0 for a link to remove it (e.g. container_id=0 unlinks the task from its bed).
    Rescheduling remind_at lets it fire again even if the previous reminder already went out.
    To change status, use update_task_status."""
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

        container_id, planting_id, variety_id = await _resolve_task_links(
            db, user, container_id, planting_id, variety_id
        )
        for field, value in (
            ("container_id", container_id),
            ("planting_id", planting_id),
            ("variety_id", variety_id),
        ):
            if value is not None:
                setattr(task, field, value or None)

        await db.commit()
        return _task_dict(task)


@mcp_server.tool()
async def create_category(
    name: str,
    color: str,
    harvest_type: str = "continuous",
    harvest_unit: str | None = None,
    plants_per_square: int | None = None,
    icon_svg: str | None = None,
    planting_seasons: list[dict] | None = None,
) -> dict:
    """Add a new plant category to the catalog (global — shared across every user of this
    Tendril instance, like Tomatoes or Peppers). color is a hex string like '#FF5733'.
    harvest_type must be 'single' (one harvest ends the planting, e.g. a head of lettuce),
    'continuous' (repeated harvests over time, e.g. tomatoes), or 'none' (not harvested
    for food, e.g. ornamental flowers — left out of the harvest forecast). harvest_unit (a
    singular noun for one plant's harvest: head, bunch, root) and plants_per_square (plants in
    one planting's footprint, square-foot-gardening style: 16 carrots, 1 broccoli) are the
    harvest forecast defaults every variety in the category inherits; the unit mostly matters
    for single-harvest crops. Each planting_seasons entry needs usda_zone, start_month,
    start_day, end_month, end_day — this garden is Zone 10a."""
    if harvest_type not in VALID_HARVEST_TYPES:
        raise ToolError(f"harvest_type must be one of: {', '.join(sorted(VALID_HARVEST_TYPES))}")
    _validate_harvest_fields(None, plants_per_square)

    async with async_session() as db:
        await get_mcp_user(db)

        existing = await db.execute(select(Category).where(Category.name == name))
        if existing.scalar_one_or_none():
            raise ToolError(f"Category '{name}' already exists")

        category = Category(
            name=name,
            color=color,
            harvest_type=harvest_type,
            harvest_unit=(harvest_unit or "").strip() or None,
            plants_per_square=plants_per_square,
            icon_svg=icon_svg,
        )
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
    harvest_unit: str | None = None,
    plants_per_square: int | None = None,
    icon_svg: str | None = None,
    planting_seasons: list[dict] | None = None,
) -> dict:
    """Update a category's fields — only the ones you pass are changed. Passing
    planting_seasons replaces the category's entire season list (each entry needs
    usda_zone, start_month, start_day, end_month, end_day). harvest_unit and
    plants_per_square are the harvest forecast defaults its varieties inherit (see
    create_category); pass harvest_unit='' or plants_per_square=0 to clear one."""
    if harvest_type is not None and harvest_type not in VALID_HARVEST_TYPES:
        raise ToolError(f"harvest_type must be one of: {', '.join(sorted(VALID_HARVEST_TYPES))}")
    _validate_harvest_fields(None, plants_per_square, allow_clear=True)

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
        _apply_harvest_count_fields(category, harvest_unit, plants_per_square)
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


@mcp_server.tool()
async def update_container(
    container_id: int,
    name: str | None = None,
    location_description: str | None = None,
    irrigation_type: str | None = None,
    irrigation_duration_minutes: int | None = None,
    irrigation_frequency: str | None = None,
) -> dict:
    """Rename a container (grid bed or tower) or change its location description or irrigation
    setup. Only the fields you pass are changed. irrigation_type must be one of: drip, manual,
    sprinkler; irrigation_frequency one of: daily, 2x_daily, every_2_days, every_3_days, weekly.
    Size/shape (width, height, levels, pockets) can't be changed here — resizing could strand
    plantings outside the grid, so that stays in the app's edit form."""
    if irrigation_type is not None and irrigation_type not in VALID_IRRIGATION_TYPES:
        raise ToolError(f"irrigation_type must be one of: {', '.join(sorted(VALID_IRRIGATION_TYPES))}")
    if irrigation_frequency is not None and irrigation_frequency not in VALID_IRRIGATION_FREQUENCIES:
        raise ToolError(
            f"irrigation_frequency must be one of: {', '.join(sorted(VALID_IRRIGATION_FREQUENCIES))}"
        )
    if irrigation_duration_minutes is not None and irrigation_duration_minutes <= 0:
        raise ToolError("irrigation_duration_minutes must be positive")
    if name is not None and not name.strip():
        raise ToolError("name can't be blank")

    async with async_session() as db:
        user = await get_mcp_user(db)
        result = await db.execute(
            select(Container).where(Container.id == container_id, Container.user_id == user.id)
        )
        container = result.scalar_one_or_none()
        if not container:
            raise ToolError(f"Container {container_id} not found")

        updates = {
            "name": name.strip() if name is not None else None,
            "location_description": location_description,
            "irrigation_type": irrigation_type,
            "irrigation_duration_minutes": irrigation_duration_minutes,
            "irrigation_frequency": irrigation_frequency,
        }
        for field, value in updates.items():
            if value is not None:
                setattr(container, field, value)

        await db.commit()
        return _container_dict(container)
