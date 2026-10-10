"""Week-by-week harvest forecast — what's expected to come out of the garden when.

Built for kitchen planning (what to cook/can/freeze), not yield tracking, so output is
counts and words ("Snowball Cauliflower: 2 heads", "Sweet Banana Pepper: continuous")
rather than weights.

Rules:
  - harvest_type comes from the variety override, else its category. "none" (ornamentals,
    cover crops) is left out entirely.
  - Single-harvest plantings land in the week of their end_date — the day they're pulled.
  - Continuous plantings appear in every week of [harvest start, end_date], with harvest
    start computed the same way as the lifecycle "harvesting" phase.
  - Count = planting.quantity, falling back to plants_per_square (variety, else category);
    if none is set the planting is counted as "1 planting". harvest_unit inherits the same way.
  - Complete plantings are excluded. An in-progress planting whose end_date has already
    passed is listed in the first week only, flagged overdue — it's still in the ground,
    either waiting to be picked (single) or still producing (continuous).

Weeks run Monday–Sunday.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.planting import Planting
from app.models.variety import Variety
from app.services.lifecycle import compute_harvest_start


@dataclass
class _Item:
    variety_id: int
    variety_name: str
    category_name: str
    category_color: str
    harvest_type: str
    unit: str | None
    count: int = 0
    uncounted_plantings: int = 0
    starting: bool = False
    ending: bool = False
    overdue: bool = False
    plantings: list[dict] = field(default_factory=list)


def pluralize(unit: str, count: int) -> str:
    if count == 1:
        return unit
    if unit.endswith(("s", "sh", "ch", "x", "z")):
        return unit + "es"
    if unit.endswith("y") and unit[-2:-1] not in "aeiou":
        return unit[:-1] + "ies"
    return unit + "s"


def _label(item: _Item) -> str:
    if item.harvest_type == "continuous":
        text = f"{item.variety_name}: continuous"
        if item.overdue:
            text += " (past planned end)"
        elif item.starting and item.ending:
            text += " (starts and ends this week)"
        elif item.starting:
            text += " (starts this week)"
        elif item.ending:
            text += " (last week)"
        return text

    parts = []
    if item.count:
        parts.append(f"{item.count} {pluralize(item.unit, item.count)}" if item.unit else str(item.count))
    if item.uncounted_plantings:
        n = item.uncounted_plantings
        parts.append(f"{n} planting{'s' if n != 1 else ''}")
    text = f"{item.variety_name}: {' + '.join(parts)}"
    if item.overdue:
        text += " (overdue)"
    return text


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


async def get_harvest_forecast(
    db: AsyncSession,
    user_id: int,
    start: date,
    weeks: int,
) -> list[dict]:
    """Return `weeks` Monday–Sunday buckets starting with the week containing `start`."""
    first_week = _week_start(start)
    range_end = first_week + timedelta(weeks=weeks)  # exclusive

    stmt = (
        select(Planting)
        .options(
            selectinload(Planting.variety).selectinload(Variety.category),
            selectinload(Planting.container),
        )
        .where(
            Planting.user_id == user_id,
            Planting.status != "complete",
            Planting.start_date < range_end,
        )
    )
    plantings = (await db.execute(stmt)).scalars().all()
    return build_forecast(plantings, start, weeks)


def build_forecast(plantings: Sequence[Planting], start: date, weeks: int) -> list[dict]:
    """Bucket already-loaded plantings (variety, category, container loaded) into weeks.

    Split from the query so the date logic can be tested without a database.
    """
    first_week = _week_start(start)
    range_end = first_week + timedelta(weeks=weeks)  # exclusive

    # week index -> (variety_id, harvest_type) -> item
    buckets: list[dict[tuple[int, str], _Item]] = [{} for _ in range(weeks)]

    def add(week_idx: int, p: Planting, htype: str, detail: dict) -> _Item:
        v = p.variety
        key = (v.id, htype)
        item = buckets[week_idx].get(key)
        if item is None:
            item = _Item(
                variety_id=v.id,
                variety_name=v.name,
                category_name=v.category.name,
                category_color=v.category.color,
                harvest_type=htype,
                unit=v.effective_harvest_unit,
            )
            buckets[week_idx][key] = item
        item.plantings.append(detail)
        return item

    for p in plantings:
        v = p.variety
        htype = v.effective_harvest_type
        if htype == "none":
            continue

        count = p.quantity or v.effective_plants_per_square
        detail = {
            "planting_id": p.id,
            "container_id": p.container_id,
            "container_name": p.container.name if p.container else None,
            "square_x": p.square_x,
            "square_y": p.square_y,
            "tower_level": p.tower_level,
            "status": p.status,
            "count": count,
        }

        if htype == "single":
            harvest_date = p.end_date
            overdue = harvest_date < first_week
            if overdue and p.status != "in_progress":
                continue  # a planned planting whose dates have passed never went in
            if harvest_date >= range_end:
                continue
            week_idx = 0 if overdue else (harvest_date - first_week).days // 7
            item = add(week_idx, p, htype, {**detail, "harvest_date": harvest_date.isoformat()})
            if count:
                item.count += count
            else:
                item.uncounted_plantings += 1
            item.overdue = item.overdue or overdue
        else:
            window_end = p.end_date
            window_start = min(
                compute_harvest_start(
                    p.start_date, v.days_to_harvest_min, v.days_to_harvest_max, p.seed_start_date
                ),
                window_end,
            )
            overdue = window_end < first_week
            if overdue and p.status != "in_progress":
                continue
            if window_start >= range_end:
                continue
            first_idx = max((window_start - first_week).days // 7, 0)
            last_idx = 0 if overdue else min((window_end - first_week).days // 7, weeks - 1)
            for week_idx in range(first_idx, last_idx + 1):
                wk_start = first_week + timedelta(weeks=week_idx)
                wk_end = wk_start + timedelta(days=6)
                item = add(
                    week_idx,
                    p,
                    htype,
                    {
                        **detail,
                        "harvest_start": window_start.isoformat(),
                        "harvest_end": window_end.isoformat(),
                    },
                )
                if count:
                    item.count += count
                else:
                    item.uncounted_plantings += 1
                item.starting = item.starting or wk_start <= window_start <= wk_end
                item.ending = item.ending or wk_start <= window_end <= wk_end
                item.overdue = item.overdue or overdue

    result = []
    for week_idx, bucket in enumerate(buckets):
        wk_start = first_week + timedelta(weeks=week_idx)
        # Single harvests first (they're the ones that need a plan), then alphabetical
        items = sorted(bucket.values(), key=lambda i: (i.harvest_type != "single", i.variety_name.lower()))
        result.append(
            {
                "week_start": wk_start.isoformat(),
                "week_end": (wk_start + timedelta(days=6)).isoformat(),
                "items": [
                    {
                        "label": _label(i),
                        "variety_id": i.variety_id,
                        "variety_name": i.variety_name,
                        "category_name": i.category_name,
                        "category_color": i.category_color,
                        "harvest_type": i.harvest_type,
                        "unit": i.unit,
                        "count": i.count or None,
                        "uncounted_plantings": i.uncounted_plantings,
                        "starting": i.starting,
                        "ending": i.ending,
                        "overdue": i.overdue,
                        "plantings": i.plantings,
                    }
                    for i in items
                ],
            }
        )
    return result
