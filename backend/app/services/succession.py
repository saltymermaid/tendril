"""Overdue plantings, and the planned plantings waiting for their squares.

A planting is overdue once it's still in_progress on or after its estimated end_date.
It keeps its squares until it's marked complete, so any not_started planting planned
on those squares is waiting on it.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.planting import Planting


def is_overdue(p: Planting, on: date) -> bool:
    return p.status == "in_progress" and p.end_date <= on


def shares_squares(a: Planting, b: Planting) -> bool:
    """Whether two plantings sit on any of the same squares (ignoring dates)."""
    if a.container_id != b.container_id or a.tower_level != b.tower_level:
        return False
    return (
        a.square_x < b.square_x + b.square_width
        and b.square_x < a.square_x + a.square_width
        and a.square_y < b.square_y + b.square_height
        and b.square_y < a.square_y + a.square_height
    )


async def next_plantings_for_overdue(
    db: AsyncSession, plantings: list[Planting], on: date
) -> dict[int, Planting]:
    """For each overdue planting in `plantings`, the earliest planned planting waiting on any
    of its squares (keyed by the overdue planting's id). Waiting plantings come back with
    their variety loaded."""
    overdue = [p for p in plantings if is_overdue(p, on)]
    if not overdue:
        return {}

    result = await db.execute(
        select(Planting)
        .options(selectinload(Planting.variety))
        .where(
            Planting.user_id == overdue[0].user_id,
            Planting.container_id.in_({p.container_id for p in overdue}),
            Planting.status == "not_started",
        )
        .order_by(Planting.start_date)
    )
    planned = result.scalars().all()

    nexts: dict[int, Planting] = {}
    for p in overdue:
        for candidate in planned:
            if candidate.start_date >= p.start_date and shares_squares(p, candidate):
                nexts[p.id] = candidate
                break
    return nexts
