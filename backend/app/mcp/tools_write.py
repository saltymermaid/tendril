"""Narrow write MCP tools — create a planting, complete a planting, create a task,
change a task's status, create a plant start. No deletes, no variety/container/yard/plant-start
mutations beyond creation, by design (see the plan's confirmed v1 write scope).

Validation is reused, not duplicated: `_check_overlap` and `validate_planting_bounds`
are imported directly from the REST plantings router so the two entry points can't
drift. Both raise `HTTPException` (a plain exception class, safe to raise outside a
route handler) — caught here and re-raised as `ToolError` so the message reaches the
MCP client (a plain `ValueError` would be masked by the SDK into a generic
"Error executing tool X" with no detail — see mcp/server/mcpserver/tools/base.py).
"""

from datetime import date

from fastapi import HTTPException
from mcp.server.mcpserver.exceptions import ToolError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.mcp.server import mcp_server
from app.mcp.context import get_mcp_user
from app.models.container import Container
from app.models.plant_start import PlantStart
from app.models.planting import Planting
from app.models.task import Task
from app.models.variety import Variety
from app.mcp.tools_read import _planting_dict, _plant_start_dict
from app.routers.plantings import _check_overlap, _consume_plant_start, validate_planting_bounds

VALID_REMOVAL_REASONS = {"harvest_complete", "died", "pulled_early", "pest_disease", "other"}


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


@mcp_server.tool()
async def create_task(
    title: str,
    description: str | None = None,
    due_date: date | None = None,
    container_id: int | None = None,
    planting_id: int | None = None,
    variety_id: int | None = None,
) -> dict:
    """Create a manual task (source is always 'manual' — auto tasks come from the task generator)."""
    async with async_session() as db:
        user = await get_mcp_user(db)
        task = Task(
            user_id=user.id,
            title=title,
            description=description,
            due_date=due_date,
            source="manual",
            container_id=container_id,
            planting_id=planting_id,
            variety_id=variety_id,
        )
        db.add(task)
        await db.commit()
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": due_date.isoformat() if due_date else None,
            "source": task.source,
            "status": task.status,
            "container_id": task.container_id,
            "planting_id": task.planting_id,
            "variety_id": task.variety_id,
        }


@mcp_server.tool()
async def update_task_status(task_id: int, status: str) -> dict:
    """Mark a task completed or dismissed. status must be one of: completed, dismissed."""
    if status not in ("completed", "dismissed"):
        raise ToolError("status must be 'completed' or 'dismissed'")

    async with async_session() as db:
        user = await get_mcp_user(db)
        result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
        task = result.scalar_one_or_none()
        if not task:
            raise ToolError(f"Task {task_id} not found")

        task.status = status
        await db.commit()
        return {"id": task.id, "title": task.title, "status": task.status}
