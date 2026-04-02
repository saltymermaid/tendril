"""Recommendations router — 'What can I plant here?' endpoint."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.recommendations import get_recommendations

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("")
async def recommend(
    container_id: int = Query(..., description="Container ID"),
    square_x: int = Query(..., description="Target square X coordinate"),
    square_y: int = Query(..., description="Target square Y coordinate"),
    target_date: date = Query(None, alias="date", description="Date to check (defaults to today)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get planting recommendations for a specific square."""
    check_date = target_date or date.today()

    results = await get_recommendations(
        db=db,
        user_id=current_user.id,
        container_id=container_id,
        square_x=square_x,
        square_y=square_y,
        target_date=check_date,
    )

    # Group by category
    categories: dict[int, dict] = {}
    for r in results:
        if r.category_id not in categories:
            categories[r.category_id] = {
                "category_id": r.category_id,
                "category_name": r.category_name,
                "category_color": r.category_color,
                "varieties": [],
            }
        categories[r.category_id]["varieties"].append({
            "variety_id": r.variety_id,
            "variety_name": r.variety_name,
            "score": round(r.score, 1),
            "days_to_harvest_min": r.days_to_harvest_min,
            "days_to_harvest_max": r.days_to_harvest_max,
            "planting_method": r.planting_method,
            "is_climbing": r.is_climbing,
            "spacing": r.spacing,
            "warnings": r.warnings,
            "boosts": r.boosts,
        })

    # Sort categories by best variety score
    sorted_categories = sorted(
        categories.values(),
        key=lambda c: max(v["score"] for v in c["varieties"]),
        reverse=True,
    )

    return {
        "date": check_date.isoformat(),
        "container_id": container_id,
        "square_x": square_x,
        "square_y": square_y,
        "total_varieties": len(results),
        "categories": sorted_categories,
    }
