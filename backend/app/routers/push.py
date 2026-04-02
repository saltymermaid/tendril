"""Push subscription router — Web Push API subscription management."""

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


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh_key: str
    auth_key: str


class PushSubscriptionResponse(BaseModel):
    id: int
    endpoint: str

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
        return PushSubscriptionResponse(id=existing.id, endpoint=existing.endpoint)

    sub = PushSubscription(
        user_id=user.id,
        endpoint=body.endpoint,
        p256dh_key=body.p256dh_key,
        auth_key=body.auth_key,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return PushSubscriptionResponse(id=sub.id, endpoint=sub.endpoint)


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
    """List all push subscriptions for the current user."""
    result = await db.execute(
        select(PushSubscription).where(PushSubscription.user_id == user.id)
    )
    subs = result.scalars().all()
    return [PushSubscriptionResponse(id=s.id, endpoint=s.endpoint) for s in subs]
