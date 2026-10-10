"""Harvest forecast router — week-by-week list of what's expected to be picked."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.harvest_forecast import get_harvest_forecast

router = APIRouter(prefix="/api/harvest-forecast", tags=["harvest"])


@router.get("")
async def harvest_forecast(
    start: date | None = Query(None, description="Any date in the first week (defaults to today)"),
    weeks: int = Query(8, ge=1, le=52, description="Number of Monday–Sunday weeks to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Expected harvests grouped by week and variety."""
    return {
        "weeks": await get_harvest_forecast(db, current_user.id, start or date.today(), weeks),
    }
