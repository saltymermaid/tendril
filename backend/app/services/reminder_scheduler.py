"""Background loop that fires push notifications for due task reminders.

A single-user, self-hosted app doesn't need a task queue for this — an asyncio loop
started alongside the FastAPI app is enough. Runs on a fixed interval rather than
scheduling each reminder individually, so a missed tick (e.g. a restart) just catches
up on the next pass instead of losing the reminder.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import async_session
from app.models.task import Task
from app.services.push import send_push_to_user

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 60


async def send_due_reminders() -> int:
    """Push-notify for each pending task whose remind_at has passed. Returns count sent."""
    now = datetime.now(timezone.utc)
    sent = 0

    async with async_session() as db:
        stmt = select(Task).where(
            Task.remind_at.is_not(None),
            Task.remind_at <= now,
            Task.reminder_sent.is_(False),
            Task.status == "pending",
        )
        result = await db.execute(stmt)
        tasks = result.scalars().all()

        for task in tasks:
            count = await send_push_to_user(
                db,
                user_id=task.user_id,
                title="🌱 Tendril reminder",
                body=task.title,
                url="/tasks",
                tag=f"task-{task.id}",
            )
            task.reminder_sent = True
            if count:
                sent += 1

        if tasks:
            await db.commit()

    return sent


async def reminder_scheduler_loop() -> None:
    """Run send_due_reminders on a fixed interval until cancelled."""
    while True:
        try:
            await send_due_reminders()
        except Exception:
            logger.exception("Reminder scheduler tick failed")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
