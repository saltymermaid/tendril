"""Task auto-generation service.

Scans plantings and creates tasks for:
- Harvest window alerts (in_progress plantings approaching harvest)
- Upcoming planting reminders (not_started plantings with start_date approaching)
- Germination check-ins (recently activated plantings)

Idempotent: only creates tasks if a matching pending task doesn't already exist.
"""

import logging
from datetime import date, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.planting import Planting
from app.models.task import Task
from app.models.user import User

logger = logging.getLogger(__name__)


async def generate_tasks_for_user(db: AsyncSession, user_id: int) -> int:
    """Generate auto tasks for a single user. Returns count of new tasks created."""
    today = date.today()
    created_count = 0

    # Load all active plantings with variety info
    stmt = (
        select(Planting)
        .options(selectinload(Planting.variety), selectinload(Planting.container))
        .where(
            Planting.user_id == user_id,
            Planting.status.in_(["not_started", "in_progress"]),
        )
    )
    result = await db.execute(stmt)
    plantings = result.scalars().all()

    # Load existing pending auto tasks for this user to check for duplicates
    existing_stmt = select(Task).where(
        Task.user_id == user_id,
        Task.source == "auto",
        Task.status == "pending",
    )
    existing_result = await db.execute(existing_stmt)
    existing_tasks = existing_result.scalars().all()

    # Build a set of (planting_id, title_prefix) for dedup
    existing_keys = set()
    for t in existing_tasks:
        # Use first 40 chars of title + planting_id as dedup key
        key = (t.planting_id, t.title[:40] if t.title else "")
        existing_keys.add(key)

    for planting in plantings:
        variety_name = planting.variety.name if planting.variety else "Unknown"
        container_name = planting.container.name if planting.container else "Unknown"

        if planting.status == "not_started":
            # Upcoming planting reminder: 3 days before start_date
            days_until_start = (planting.start_date - today).days
            if 0 <= days_until_start <= 3:
                title = f"🌱 Time to plant {variety_name}"
                key = (planting.id, title[:40])
                if key not in existing_keys:
                    task = Task(
                        user_id=user_id,
                        title=title,
                        description=f"Plant {variety_name} in {container_name}. Scheduled start: {planting.start_date}.",
                        due_date=planting.start_date,
                        source="auto",
                        container_id=planting.container_id,
                        planting_id=planting.id,
                        variety_id=planting.variety_id,
                    )
                    db.add(task)
                    existing_keys.add(key)
                    created_count += 1

        elif planting.status == "in_progress":
            # Germination check-in: 7-14 days after activation
            # We use start_date as proxy for activation date
            days_since_start = (today - planting.start_date).days

            # Germination check (around day 7-10)
            germ_min = planting.variety.days_to_germination_min if planting.variety else None
            germ_max = planting.variety.days_to_germination_max if planting.variety else None
            check_day = germ_min or germ_max or 7

            if check_day - 1 <= days_since_start <= check_day + 2:
                title = f"🔍 Check germination: {variety_name}"
                key = (planting.id, title[:40])
                if key not in existing_keys:
                    task = Task(
                        user_id=user_id,
                        title=title,
                        description=f"Check if {variety_name} in {container_name} has germinated (expected {check_day} days).",
                        due_date=today,
                        source="auto",
                        container_id=planting.container_id,
                        planting_id=planting.id,
                        variety_id=planting.variety_id,
                    )
                    db.add(task)
                    existing_keys.add(key)
                    created_count += 1

            # Harvest window alert: when approaching harvest time
            harvest_min = planting.variety.days_to_harvest_min if planting.variety else None
            harvest_max = planting.variety.days_to_harvest_max if planting.variety else None

            if harvest_min:
                days_to_harvest = harvest_min - days_since_start
                if -3 <= days_to_harvest <= 5:
                    title = f"🌾 Harvest window: {variety_name}"
                    key = (planting.id, title[:40])
                    if key not in existing_keys:
                        harvest_range = f"{harvest_min}"
                        if harvest_max and harvest_max != harvest_min:
                            harvest_range = f"{harvest_min}-{harvest_max}"
                        task = Task(
                            user_id=user_id,
                            title=title,
                            description=f"{variety_name} in {container_name} is approaching harvest time ({harvest_range} days from planting).",
                            due_date=planting.start_date + timedelta(days=harvest_min),
                            source="auto",
                            container_id=planting.container_id,
                            planting_id=planting.id,
                            variety_id=planting.variety_id,
                        )
                        db.add(task)
                        existing_keys.add(key)
                        created_count += 1

    await db.flush()
    return created_count


async def generate_all_tasks(db: AsyncSession) -> int:
    """Generate auto tasks for all users. Returns total count of new tasks."""
    result = await db.execute(select(User.id))
    user_ids = [row[0] for row in result.all()]

    total = 0
    for uid in user_ids:
        count = await generate_tasks_for_user(db, uid)
        total += count

    if total > 0:
        logger.info("Auto-generated %d tasks across %d users", total, len(user_ids))

    return total
