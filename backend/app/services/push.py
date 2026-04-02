"""Push notification service — Web Push API via pywebpush."""

import json
import logging

from pywebpush import webpush, WebPushException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


async def send_push_to_user(
    db: AsyncSession,
    user_id: int,
    title: str,
    body: str,
    url: str = "/",
    tag: str = "tendril-notification",
) -> int:
    """Send a push notification to all subscriptions for a user.

    Returns the number of successfully sent notifications.
    """
    settings = get_settings()
    if not settings.vapid_private_key or not settings.vapid_public_key:
        logger.warning("VAPID keys not configured — skipping push notification")
        return 0

    result = await db.execute(
        select(PushSubscription).where(PushSubscription.user_id == user_id)
    )
    subscriptions = result.scalars().all()

    if not subscriptions:
        return 0

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
        "tag": tag,
    })

    sent = 0
    stale_ids: list[int] = []

    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.p256dh_key,
                "auth": sub.auth_key,
            },
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": f"mailto:{settings.allowed_emails.split(',')[0].strip() or 'admin@tendril.app'}"},
            )
            sent += 1
        except WebPushException as e:
            logger.warning("Push failed for subscription %d: %s", sub.id, e)
            # If subscription is gone (410 Gone or 404), mark for removal
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code in (404, 410):
                    stale_ids.append(sub.id)
        except Exception as e:
            logger.error("Unexpected push error for subscription %d: %s", sub.id, e)

    # Clean up stale subscriptions
    if stale_ids:
        for sub_id in stale_ids:
            result = await db.execute(
                select(PushSubscription).where(PushSubscription.id == sub_id)
            )
            stale_sub = result.scalar_one_or_none()
            if stale_sub:
                await db.delete(stale_sub)
        await db.commit()
        logger.info("Removed %d stale push subscriptions", len(stale_ids))

    return sent
