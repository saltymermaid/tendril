"""Push subscription router — Web Push API subscription management."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.push_subscription import PushSubscription
from app.models.user import User

router = APIRouter(prefix="/api/push", tags=["push"])

# Each browser's push service has a distinct endpoint host — good enough to label
# "which device is this" in a subscription list without storing a user agent.
_ENDPOINT_PLATFORM_HINTS = (
    ("web.push.apple.com", "Safari / iOS"),
    ("fcm.googleapis.com", "Chrome / Android"),
    ("android.googleapis.com", "Chrome / Android"),
    ("notify.windows.com", "Edge / Windows"),
    ("updates.push.services.mozilla.com", "Firefox"),
)


def _platform_label(endpoint: str) -> str:
    for hint, label in _ENDPOINT_PLATFORM_HINTS:
        if hint in endpoint:
            return label
    return "Unknown browser"


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh_key: str
    auth_key: str


class PushSubscriptionResponse(BaseModel):
    id: int
    endpoint: str
    platform: str
    created_at: datetime

    model_config = {"from_attributes": True}


class VapidPublicKeyResponse(BaseModel):
    public_key: str


@router.get("/vapid-public-key", response_model=VapidPublicKeyResponse)
async def get_vapid_public_key():
    """Return the VAPID public key for the frontend to use when subscribing."""
    settings = get_settings()
    if not settings.vapid_public_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Push notifications not configured",
        )
    return VapidPublicKeyResponse(public_key=settings.vapid_public_key)


@router.post("/subscribe", response_model=PushSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def subscribe(
    body: PushSubscriptionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save a push subscription for the current user.

    If the same endpoint already exists for this user, update the keys.
    """
    # Check for existing subscription with same endpoint
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == user.id,
            PushSubscription.endpoint == body.endpoint,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.p256dh_key = body.p256dh_key
        existing.auth_key = body.auth_key
        await db.commit()
        await db.refresh(existing)
        return PushSubscriptionResponse(
            id=existing.id,
            endpoint=existing.endpoint,
            platform=_platform_label(existing.endpoint),
            created_at=existing.created_at,
        )

    sub = PushSubscription(
        user_id=user.id,
        endpoint=body.endpoint,
        p256dh_key=body.p256dh_key,
        auth_key=body.auth_key,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return PushSubscriptionResponse(
        id=sub.id, endpoint=sub.endpoint, platform=_platform_label(sub.endpoint), created_at=sub.created_at
    )


@router.delete("/subscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe(
    body: PushSubscriptionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a push subscription for the current user."""
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == user.id,
            PushSubscription.endpoint == body.endpoint,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        await db.delete(existing)
        await db.commit()


@router.get("/subscriptions", response_model=list[PushSubscriptionResponse])
async def list_subscriptions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all push subscriptions for the current user, oldest first."""
    result = await db.execute(
        select(PushSubscription)
        .where(PushSubscription.user_id == user.id)
        .order_by(PushSubscription.created_at.asc())
    )
    subs = result.scalars().all()
    return [
        PushSubscriptionResponse(
            id=s.id, endpoint=s.endpoint, platform=_platform_label(s.endpoint), created_at=s.created_at
        )
        for s in subs
    ]


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a single push subscription by id (e.g. a stale device from the settings page)."""
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.id == subscription_id,
            PushSubscription.user_id == user.id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    await db.delete(sub)
    await db.commit()
